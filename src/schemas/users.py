from pydantic import BaseModel,Field




#定义用户请求模型
class UserInfoRequest(BaseModel):
    username:str=Field(default=None,description='用户名')



class UserInfoResponse(BaseModel):
    code:int=Field(default=200,description='返回状态码')
    message:str=Field(default=None,description='返回信息')
    data:list[str]=Field(default=None,description='返回数据')