from pydantic import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    KAFKA_BOOTSTRAP_SERVERS: str
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str
    ALGORITHM = "HS256"
    PROJECT_NAME = "Whatsapp Bot"
    RAZORPAY_API_KEY: str
    RAZORPAY_API_SECRET: str
    RAZORPAY_PAYMENT_LINK: str
    RAZORPAY_WEBHOOK_SECRET: str
    CALENDLY_TOKEN: str
    CALENDLY_SINGLE_USE_LINK: str
    CALENDLY_OWNER: str
    AZURE_APPINSIGHTS_INSTRUMENTATIONKEY: str
    WATOKEN: str
    NUMBER_ID: str
    APP_ID: str
    WHATSAPP_BUSINESS_ID: str
    TOKEN: str
    CONNECTION_STRING: str
    AZURE_CONTAINER_NAME: str = "whatsapp-media"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
