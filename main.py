from llama_index.llms.ollama import Ollama # type: ignore
from llama_parse import LlamaParse # type: ignore
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, PromptTemplate # type: ignore
from llama_index.core.embeddings import resolve_embed_model # type: ignore
from llama_index.core.tools import QueryEngineTool, ToolMetadata # type: ignore
from llama_index.core.agent import ReActAgent # type: ignore
from pydantic import BaseModel
from llama_index.core.output_parsers import PydanticOutputParser # type: ignore
from llama_index.core.query_pipeline import QueryPipeline # type: ignore
from prompts import context, code_parser_template
from code_reader import code_reader
from dotenv import load_dotenv # type: ignore
import os
import ast

load_dotenv()

llm = Ollama(model="mistral", request_timeout=500.0)
parser = LlamaParse(result_type="markdown")

file_extractor = {".pdf": parser}
documents = SimpleDirectoryReader("./data", file_extractor=file_extractor).load_data()

embed_model = resolve_embed_model("local:BAAI/bge-m3")
vector_index = VectorStoreIndex.from_documents(documents, embed_model=embed_model)
query_engine = vector_index.as_query_engine(llm=llm)

# result = query_engine.query("What are the some of the routes in the API?")
# print(result)

tools = [
    QueryEngineTool(
        query_engine=query_engine,
        metadata=ToolMetadata(
            name="api_documentation",
            description="this gives documentation about code for an API. Use this for reading docs for the API",
        ),
    ),
    code_reader,
]

code_llm = Ollama(model="codellama", request_timeout=500.0)
agent = ReActAgent.from_tools(tools, llm=code_llm, verbose=True, context=context)

class CodeOutput(BaseModel):
    code: str
    description: str
    filename: str

parser = PydanticOutputParser(CodeOutput)
json_prompt_str = parser.format(code_parser_template)
json_prompt_tmpl = PromptTemplate(json_prompt_str)
output_pipeline = QueryPipeline(chain=[json_prompt_tmpl, llm])

while (prompt := input("Enter a prompt (q to quit): ")) != "q":
    retries = 0
    while retries < 3:
        try:
            result = agent.query(prompt)
            print(result)
            next_result = output_pipeline.run(response=result)
            cleaned_json = ast.literal_eval(str(next_result).replace("assistant:", ""))
            break
        except Exception as e:
            retries += 1
            print(f"Error occured, retry #{retries}:", e)

    if retries >= 3:
        print("Unable to process request, try again...")
        continue

    print("Code generated")
    print(cleaned_json["code"])
    print("\n\nDesciption:", cleaned_json["description"])

    filename = cleaned_json["filename"]

    try:
        with open(os.path.join("output", filename), "w") as f:
            f.write(cleaned_json["code"])
        print("Saved file", filename)
    except:
        print("Error saving file...")