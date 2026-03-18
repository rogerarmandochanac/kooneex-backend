from channels.generic.websocket import AsyncJsonWebsocketConsumer

class MototaxiConsumer(AsyncJsonWebsocketConsumer):
    """El pasajero envia al mototaxista"""
    async def connect(self):
        self.group_name = "mototaxistas"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def nuevo_viaje(self, event):
        await self.send_json({
            "type": "nuevo_viaje",
            "data": event["data"]
        })
    
    async def cancelar_viaje(self, event):
        await self.send_json({
            "type":"cancelar_viaje",
            "data" : event["data"]
        })


class ViajeConsumer(AsyncJsonWebsocketConsumer):
    """El mototaxista envia al pasajero"""
    async def connect(self):
        self.viaje_id = self.scope["url_route"]["kwargs"]["viaje_id"]
        self.group_name = f"viaje_{self.viaje_id}"

        print("🔌 WS conectado al grupo:", self.group_name)
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def nueva_oferta(self, event):
        await self.send_json({
            "type": "nueva_oferta",
            "data": event["data"]
        })
    
    async def oferta_cancelada(self, event):
        await self.send_json({
            "type": "oferta_cancelada",
            "data": event["data"]
        })

    async def oferta_aceptada(self, event):
        await self.send_json({
            "type": "oferta_aceptada",
            "data": event["data"]
        })

    async def viaje_cancelado(self, event):
        await self.send_json({
            "type": "viaje_cancelado",
            "data": event["data"]
        })
    
    async def viaje_en_curso(self, event):
        await self.send_json({
            "type":"viaje_en_curso",
            "data":event["data"]
        })
    
    async def viaje_completado(self, event):
        await self.send_json({
            "type":"viaje_completado",
            "data":event["data"]
    })