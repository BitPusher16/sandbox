from fastapi import FastAPI
from enum import Enum

class ModelName(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"

fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Baz"}]

# http://127.0.0.1:8000/docs
app = FastAPI()

# http://127.0.0.1:8000/
@app.get("/")
async def root():
    return {"message": "Hello World!"}

# http://127.0.0.1:8000/items/1234
@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id}

# http://127.0.0.1:8000/models/alexnet
@app.get("/models/{model_name}")
async def get_model(model_name: ModelName):
    if model_name is ModelName.alexnet:
        return {"model_name": model_name, "message": "Deep Learning FTW!"}
    if model_name.value == "lenet":
        return {"model_name": model_name, "message": "LeCNN all the images"}
    return {"model_name": model_name, "message": "Have some residuals"}

# http://127.0.0.1:8000/items
@app.get("/items/")
async def read_items(skip: int = 0, limit: int = 10):
    return fake_items_db[skip : skip + limit]


"""

###

POST https://example.com/comments HTTP/1.1
content-type: application/json

{
    "name": "sample",
    "time": "Wed, 21 Oct 2015 18:27:50 GMT"
}

"""