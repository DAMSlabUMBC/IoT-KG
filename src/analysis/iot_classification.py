from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate

class IoTClassification:
    def __init__(self):
        self.llm = ChatOllama(model="gemma3:4b")
        self.prompt = PromptTemplate.from_template(
            """
                You are an expert in identifying Internet of Things (IoT) products.
                You will be given a product name and your task is to classify the product into IOT or NOT-IOT.
                Products that should be marked as IOT are physical devices, vehicles, appliances, and other physical 
                objects that are embedded with sensors, software, and network connectivity, allowing them to collect and share data.
                Anything else should be marked as NOT-IOT.

                Strictly return IOT or NOT-IOT

                Examples:
                Amazon Echo Dot -> IOT
                Apple Watch Strap -> NOT-IOT
                Google Nest Thermostat -> IOT
                Samsung SmartThings Motion Sensor -> IOT
                Philips Hue Lightstrip -> IOT
                TP-Link Smart Plug -> IOT
                Ring Video Doorbell -> IOT
                Wyze Cam v3 -> IOT
                Garmin GPS Navigator -> IOT
                Beats Studio Headphones -> IOT
                OtterBox Phone Case -> NOT-IOT
                LG Smart Refrigerator -> IOT
                Fitbit Charge 5 -> IOT
                Anker Power Bank -> NOT-IOT
                Sony Bravia Smart TV -> IOT
                Canon EOS Rebel Camera -> NOT-IOT
                Arlo Pro 4 Spotlight Camera -> IOT
                Eero Mesh WiFi Router -> IOT
                Belkin Surge Protector -> NOT-IOT
                Echo Wall Clock -> IOT
                Logitech MX Master 3 Mouse -> IOT
                August Smart Lock Pro -> IOT

                Product Name: {product_name}
            """
        )
    
    def classify(self, product_name):
        print("Classify product name", product_name)
        prompt = self.prompt.format(product_name=product_name)
        response = self.llm.invoke(prompt)
        print("Classify response: ", response.content)
        return response.content