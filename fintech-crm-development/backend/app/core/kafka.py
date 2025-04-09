import json
from datetime import datetime

from aiokafka import AIOKafkaConsumer
from app.core.config import settings
from app.core.helper import extract_phone_number_and_country_code
from app.core.logger import logger
from app.core.websocket import websocket_manager, websocket_manager_notifications
from app.repository.user_repository import user_repository
from app.repository.notification_repository import notification_repository
from app.schemas.user import UserCreateKafka

class KafkaConsumer:
    """
    Kafka Consumer class to consume messages from Kafka topic
    """

    def __init__(self, loop):
        """
        :param loop: asyncio event loop

        Initialize the consumer with the event loop and Kafka settings
        having two consumers with different group id
        one for normal database query and another for websocket"""
        print("Initializing Kafka Consumers...")
        self.consumer = AIOKafkaConsumer(
            "whatsapp-bot",
            loop=loop,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id=settings.KAFKA_GROUP_ID,
        )
        self.websocketconsumer = AIOKafkaConsumer(
            "whatsapp-bot",
            loop=loop,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id=settings.KAFKA_WEBSOCKET_GROUP_ID,
        )

    async def consume(self):
        """
        Consume messages from Kafka topic and create users based on the received data.
        """
        try:
            print("Starting Kafka consumer...")
            await self.consumer.start()
            print("Kafka consumer started successfully")
        except Exception as e:
            logger.exception("Kafka consumer start failed")
            print(f"Kafka consumer start failed: {e}")
            return

        try:
            print("Consumer is now polling for messages...")
            async for msg in self.consumer:
                print(f"Raw message received: {msg}")
                try:
                    string_data = msg.value.decode("utf-8")  # Decode byte object to string
                    print(f"Decoded message: {string_data}")
                    response = json.loads(string_data)
                    print(f"Parsed JSON response: {response}")
                    
                    # Process user creation logic
                    if response.get("type") != "reminder":
                        print("Processing user creation logic...")
                        # Access phone_number from the nested 'data' field
                        phone_number = response["data"].get("phone_number")
                        if phone_number:
                            phone, country_code = extract_phone_number_and_country_code(phone_number)
                            print(f"Extracted phone: {phone}, country code: {country_code}")
                            if phone and country_code:
                                payload = UserCreateKafka(
                                    phone_number=phone,
                                    country_code=country_code,
                                    status="Consultation Initiated",
                                    source="whatsapp",
                                )
                                user_exists = await user_repository.get_by_phone(phone)
                                print(f"User exists: {user_exists}")
                                if not user_exists:
                                    await user_repository.create(payload)
                                    print("New user created successfully")
                                await user_repository.update_last_communication(phone, response["data"]["timestamp"])
                                print("Updated last communication timestamp")
                            else:
                                print("Could not extract valid phone number and country code")
                        else:
                            print("No phone_number found in message data")
                        print("User creation logic processing completed")
                    
                    # Process notifications
                    print("Processing notifications...")
                    notification_data = self.format_notification(response)
                    print(f"Formatted notification data: {notification_data}")
                    if notification_data:
                        # Save to database
                        await notification_repository.create(notification_data)
                        print("Notification saved to database")
                        # Broadcast via WebSocket
                        await websocket_manager_notifications.broadcast(json.dumps(notification_data))
                        print("Notification broadcasted via WebSocket")
                    print("Notification processing completed")
                
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}")
                    print(f"Raw message value: {msg.value}")
                except KeyError as e:
                    print(f"Missing expected field in message: {e}")
                except Exception as e:
                    print(f"Error processing message: {e}")
                    raise
        except Exception as e:
            logger.exception("Kafka consumption error")
            print(f"Kafka consumption error: {e}")
        finally:
            await self.consumer.stop()
            print("Kafka consumer stopped")

    async def send_via_websocket(self):
        """
        Send messages received from Kafka to the WebSocket.
        """
        try:
            print("Starting Kafka WebSocket consumer...")
            await self.websocketconsumer.start()
            print("Kafka WebSocket consumer started successfully")
        except Exception as e:
            logger.exception("Kafka WebSocket consumer start failed")
            print(f"Kafka WebSocket consumer start failed: {e}")
            return

        try:
            print("WebSocket consumer is now polling for messages...")
            async for msg in self.websocketconsumer:
                print(f"Raw WebSocket message received: {msg}")
                try:
                    string_data = msg.value.decode("utf-8")  
                    print(f"Decoded WebSocket message: {string_data}")
                    # Send message to the WebSocket
                    await websocket_manager.broadcast(string_data)    
                    print("Message broadcasted via WebSocket")         
                except Exception as e:
                    print(f"Error processing WebSocket message: {e}")
                    raise
        except Exception as e:
            logger.exception("Kafka WebSocket consumption error")
            print(f"Kafka WebSocket consumption error: {e}")
        finally:
            await self.websocketconsumer.stop()
            print("Kafka WebSocket consumer stopped")

    def format_notification(self, data):
        print(f"Formatting notification for data: {data}")
        if data.get("type") == "reminder":
            formatted_data = {
                "type": "Reminder!",
                "details": data["data"]["message"],
                "time": data["data"]["timestamp"],
                "read": False,
                "original_data": data
            }
            print(f"Formatted reminder notification: {formatted_data}")
            return formatted_data
        elif data.get("type") == "message":
            formatted_data = {
                "type": "New Message",
                "from": data["data"]["phone_number"],
                "name": "Unknown", 
                "details": data["data"]["message_text"],
                "time": data["data"]["timestamp"],
                "read": False,
                "original_data": data
            }
            print(f"Formatted message notification: {formatted_data}")
            return formatted_data
        print("No notification formatted")
        return None