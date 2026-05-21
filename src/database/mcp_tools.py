from fastmcp import FastMCP
from queries import get_compatible_devices, get_collected_datatypes

mcp = FastMCP("IoT KG")

@mcp.tool
def get_compatible_devices_for_application(application: str) -> list:
    """Get all devices compatible with a given application"""

    answer = get_compatible_devices(application)

    return answer

@mcp.tool
def get_collected_data_for_application(application: str) -> list:
    """Retrieve all types of data an application collects given the name of an application"""

    answer = get_collected_datatypes(application)

    return answer

if __name__ == "__main__":

    # results =  get_collected_data_for_application("smartthings")

    # for result in results:
    #     print(result)
    mcp.run()