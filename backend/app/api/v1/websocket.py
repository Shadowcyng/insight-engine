from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.interactive_agent import InteractiveAgent
from app.models.upload import DataUpload
from app.db.session import SessionLocal
import structlog
import json

router = APIRouter()
log = structlog.get_logger()

async def handle_user_query(websocket: WebSocket, data: dict):
    """
    Helper to bridge the websocket message to the AI Agent.
    """
    upload_id = data.get("upload_id")
    question = data.get("question")
    
    # Minor comment: Get a fresh DB session for the query
    with SessionLocal() as db:
        upload =  db.get(DataUpload, upload_id)
        
        if not upload or not upload.file_path:
            await websocket.send_json({
                "type": "error", 
                "message": "Data context not found. Is the file uploaded?"
            })
            return

        # Minor comment: Use the consolidated Class approach
        agent = InteractiveAgent(
            upload_id=upload_id, 
            file_path=upload.file_path, 
            websocket=websocket
        )
        
        await agent.run(question=question)

@router.websocket("/logs")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    log.info("websocket_connection_established")
    
    try:
        # Minor comment: Listen for incoming messages from the React canvas
        while True:
            raw_data = await websocket.receive_text()
            data = json.loads(raw_data)
            
            # Minor comment: Route based on action type
            action = data.get("action")
            
            if action == "user_query":
                await handle_user_query(websocket, data)
            else:
                await websocket.send_json({
                    "type": "info", 
                    "message": "Message received but no action defined."
                })
                
    except WebSocketDisconnect:
        log.info("websocket_client_disconnected")
    except Exception as e:
        log.error("websocket_error", error=str(e))
        await websocket.close()