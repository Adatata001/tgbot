"""
File upload analysis handler
"""
import base64
import inspect
import logging
import os
import tempfile
from io import BytesIO
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import Config
from app.keyboards import get_main_keyboard, get_upload_keyboard
from app.services.supabase_service import supabase_service
from app.services.openai_service import OpenAIService

logger = logging.getLogger(__name__)
router = Router()
openai_service = OpenAIService()


class UploadStates(StatesGroup):
    waiting_for_file = State()


def text_has(label: str):
    return F.text.func(lambda text: isinstance(text, str) and label.lower() in text.lower())


async def read_downloaded_file(file_obj) -> bytes:
    data = file_obj.read()
    if inspect.isawaitable(data):
        data = await data
    return data


@router.message(text_has("Upload Analysis"))
@router.message(Command("upload"))
async def upload_menu(message: types.Message):
    """Show upload options."""
    await message.answer(
        "Upload Analysis\n\n"
        "Choose what you want to analyze.",
        reply_markup=get_upload_keyboard()
    )


@router.message(text_has("Back"))
async def upload_back(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Back to main menu.", reply_markup=get_main_keyboard(Config.is_admin(message.from_user)))


@router.message(text_has("Analyze Screenshot"))
async def analyze_screenshot_start(message: types.Message, state: FSMContext):
    """Start screenshot analysis flow."""
    await message.answer(
        "Send a screenshot of a trading chart, setup, signal, or indicators.\n\n"
        "Send /cancel to go back."
    )
    await state.set_state(UploadStates.waiting_for_file)
    await state.update_data(upload_type="screenshot")


@router.message(text_has("Analyze Strategy Document"))
async def analyze_strategy_start(message: types.Message, state: FSMContext):
    """Start strategy document analysis."""
    await message.answer(
        "Send your strategy document as PDF, TXT, CSV, or plain text document.\n\n"
        "Send /cancel to go back."
    )
    await state.set_state(UploadStates.waiting_for_file)
    await state.update_data(upload_type="strategy_document")


@router.message(text_has("Analyze Video"))
async def analyze_video_start(message: types.Message, state: FSMContext):
    """Start video analysis."""
    await message.answer(
        "Send a video of your chart, setup, or trading walkthrough.\n\n"
        f"I will extract up to {Config.VIDEO_FRAME_LIMIT} frames and analyze them.\n"
        "Send /cancel to go back."
    )
    await state.set_state(UploadStates.waiting_for_file)
    await state.update_data(upload_type="video")


@router.message(UploadStates.waiting_for_file, F.text)
async def handle_upload_text(message: types.Message, state: FSMContext):
    if (message.text or "").strip().lower() == "/cancel":
        await state.clear()
        await message.answer("Operation cancelled.", reply_markup=get_main_keyboard(Config.is_admin(message.from_user)))
        return

    await message.answer("Please upload the selected file type, or send /cancel.")


@router.message(UploadStates.waiting_for_file, F.photo)
async def handle_photo_upload(message: types.Message, state: FSMContext):
    """Handle photo/screenshot upload."""
    processing = await message.answer("Analyzing screenshot...")
    try:
        data = await state.get_data()
        photo = message.photo[-1]
        file_info = await message.bot.get_file(photo.file_id)
        file_obj = await message.bot.download_file(file_info.file_path)
        image_bytes = await read_downloaded_file(file_obj)
        image_base64 = base64.b64encode(image_bytes).decode()

        analysis = await analyze_image_with_vision(image_base64, data.get("upload_type", "screenshot"))
        await processing.delete()

        await message.answer(
            "Analysis Complete\n\n"
            f"{analysis}",
            reply_markup=get_main_keyboard(Config.is_admin(message.from_user))
        )

        if supabase_service.is_connected():
            await supabase_service.save_file_upload(
                user_id=message.from_user.id,
                file_id=photo.file_id,
                file_name="telegram_photo.jpg",
                file_type="photo",
                file_size=photo.file_size or 0,
                upload_type=data.get("upload_type", "screenshot"),
                analysis_result=analysis,
            )

        await state.clear()

    except Exception as e:
        logger.exception("Error processing photo")
        await processing.delete()
        await message.answer(f"Error analyzing photo: {str(e)}", reply_markup=get_main_keyboard(Config.is_admin(message.from_user)))
        await state.clear()


@router.message(UploadStates.waiting_for_file, F.document)
async def handle_document_upload(message: types.Message, state: FSMContext):
    """Handle document upload."""
    processing = await message.answer("Reading and analyzing document...")
    try:
        data = await state.get_data()
        document = message.document
        file_info = await message.bot.get_file(document.file_id)
        file_obj = await message.bot.download_file(file_info.file_path)
        file_bytes = await read_downloaded_file(file_obj)

        file_name = document.file_name or "strategy_document"
        content = extract_document_text(file_name, file_bytes)
        if not content.strip():
            await processing.delete()
            await message.answer("I could not extract text from this document.", reply_markup=get_main_keyboard(Config.is_admin(message.from_user)))
            await state.clear()
            return

        analysis = await analyze_strategy_document(content)
        await processing.delete()

        await message.answer(
            "Document Analysis\n\n"
            f"{analysis}",
            reply_markup=get_main_keyboard(Config.is_admin(message.from_user))
        )

        if supabase_service.is_connected():
            await supabase_service.save_file_upload(
                user_id=message.from_user.id,
                file_id=document.file_id,
                file_name=file_name,
                file_type=document.mime_type or "",
                file_size=document.file_size or 0,
                upload_type=data.get("upload_type", "strategy_document"),
                analysis_result=analysis,
            )

        await state.clear()

    except Exception as e:
        logger.exception("Error processing document")
        await processing.delete()
        await message.answer(f"Error analyzing document: {str(e)}", reply_markup=get_main_keyboard(Config.is_admin(message.from_user)))
        await state.clear()


@router.message(UploadStates.waiting_for_file, F.video)
async def handle_video_upload(message: types.Message, state: FSMContext):
    """Handle video upload by extracting frames and analyzing them."""
    processing = await message.answer("Extracting video frames and analyzing...")
    temp_path = ""

    try:
        data = await state.get_data()
        video = message.video
        file_info = await message.bot.get_file(video.file_id)
        file_obj = await message.bot.download_file(file_info.file_path)
        video_bytes = await read_downloaded_file(file_obj)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
            temp_file.write(video_bytes)
            temp_path = temp_file.name

        frames = extract_video_frames(temp_path, Config.VIDEO_FRAME_LIMIT)
        if not frames:
            await processing.delete()
            await message.answer("I could not extract frames from this video.", reply_markup=get_main_keyboard(Config.is_admin(message.from_user)))
            await state.clear()
            return

        prompt = (
            "Analyze these frames from a trading video. Identify the market context, visible setup, "
            "trend direction, important levels, risk concerns, and practical next steps."
        )
        analysis = await openai_service.analyze_multiple_images(frames, prompt)
        await processing.delete()

        await message.answer(
            "Video Analysis\n\n"
            f"{analysis}",
            reply_markup=get_main_keyboard(Config.is_admin(message.from_user))
        )

        if supabase_service.is_connected():
            await supabase_service.save_file_upload(
                user_id=message.from_user.id,
                file_id=video.file_id,
                file_name=video.file_name or "telegram_video.mp4",
                file_type=video.mime_type or "video/mp4",
                file_size=video.file_size or 0,
                upload_type=data.get("upload_type", "video"),
                analysis_result=analysis,
            )

        await state.clear()

    except ImportError:
        await processing.delete()
        await message.answer(
            "Video analysis requires opencv-python-headless. Run pip install -r requirements.txt.",
            reply_markup=get_main_keyboard(Config.is_admin(message.from_user))
        )
        await state.clear()
    except Exception as e:
        logger.exception("Error processing video")
        await processing.delete()
        await message.answer(f"Error analyzing video: {str(e)}", reply_markup=get_main_keyboard(Config.is_admin(message.from_user)))
        await state.clear()
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


async def analyze_image_with_vision(image_data: str, upload_type: str) -> str:
    """Analyze image with OpenAI vision."""
    prompts = {
        "screenshot": (
            "Analyze this trading chart screenshot. Provide trend context, visible indicators, "
            "support/resistance, possible setup, invalidation, risk/reward, and next steps."
        ),
        "strategy_document": (
            "Analyze this trading strategy image. Identify entry criteria, exit criteria, "
            "risk rules, weaknesses, and improvements."
        ),
        "video": (
            "Analyze this trading video frame. Describe the chart state, setup quality, "
            "key levels, and risk concerns."
        )
    }
    return await openai_service.analyze_with_vision(
        image_data,
        prompts.get(upload_type, prompts["screenshot"])
    )


async def analyze_strategy_document(content: str) -> str:
    """Analyze strategy document text."""
    prompt_context = content[:6000]
    result = await openai_service.analyze_strategy(
        strategy_text=prompt_context,
        rules="Document upload analysis",
        market_conditions="Use only the document text unless live market data is explicitly included."
    )
    if isinstance(result, dict):
        return result.get("analysis") if result.get("status") == "success" else result.get("error", "Analysis failed")
    return str(result)


def extract_document_text(file_name: str, file_bytes: bytes) -> str:
    """Extract readable text from supported document types."""
    lowered = file_name.lower()
    if lowered.endswith((".txt", ".csv", ".tsv", ".md", ".json")):
        return file_bytes.decode("utf-8", errors="ignore")
    if lowered.endswith(".pdf"):
        return extract_pdf_text(file_bytes)
    return file_bytes.decode("utf-8", errors="ignore")


def extract_pdf_text(pdf_bytes: bytes) -> str:
    """Extract text from a PDF."""
    import PyPDF2

    pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_bytes))
    pages = []
    for page in pdf_reader.pages[:10]:
        pages.append(page.extract_text() or "")
    return "\n".join(pages)


def extract_video_frames(video_path: str, frame_limit: int) -> list[dict]:
    """Extract representative frames from a video as base64 JPEG images."""
    import cv2

    capture = cv2.VideoCapture(video_path)
    if not capture.isOpened():
        return []

    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    if frame_count <= 0:
        positions = [0]
    else:
        positions = [
            int(frame_count * (index + 1) / (frame_limit + 1))
            for index in range(max(1, frame_limit))
        ]

    frames = []
    for position in positions:
        capture.set(cv2.CAP_PROP_POS_FRAMES, position)
        success, frame = capture.read()
        if not success:
            continue

        success, buffer = cv2.imencode(".jpg", frame)
        if not success:
            continue

        frames.append({
            "base64": base64.b64encode(buffer.tobytes()).decode(),
            "mime_type": "image/jpeg",
        })

    capture.release()
    return frames
