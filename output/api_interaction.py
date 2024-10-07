
import requests

# Create item
response = requests.post("http://localhost:5000/items", json={"name": "Item 1"})
print(response.json())

# Read all items
response = requests.get("http://localhost:5000/items")
print(response.json())

# Read item by ID
response = requests.get("http://localhost:5000/items/1")
print(response.json())

# Update item by ID
response = requests.put("http://localhost:5000/items/1", json={"name": "Item 2"})
print(response.json())

# Delete item by ID
response = requests.delete("http://localhost:5000/items/1")
print(response.json())
