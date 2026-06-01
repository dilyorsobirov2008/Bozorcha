import logging
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from filters.admin import IsAdmin
from keyboards.admin_kb import confirm_kb, admin_menu_kb
from states.admin_states import BroadcastState
from services.user import get_all_users

logger = logging.getLogger(__name__)
router = Router(name="admin_broadcast")
router.message.filter(IsAdmin())

# Start broadcast flow
@router.callback_query(F.data == "adm_broadcast")
async def start_broadcast(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        await state.set_state(BroadcastState.message)
        await callback.message.edit_text(
            "📢 Foydalanuvchilarga yuboriladigan xabarni kiriting:\n"
            "(Rasm, video yoki matnli xabar yuborishingiz mumkin)",
            reply_markup=None
        )
        await callback.answer()
    except Exception as e:
        logger.exception("Error starting broadcast: %s", e)
        await callback.message.answer("⚠️ Xatolik yuz berdi. Bosh menyuga qayting.")

# Receive message to broadcast
@router.message(BroadcastState.message)
async def receive_broadcast_message(message: Message, state: FSMContext) -> None:
    try:
        # Save message details to state
        if message.text:
            await state.update_data(msg_type="text", content=message.text)
        elif message.photo:
            await state.update_data(
                msg_type="photo", 
                photo_id=message.photo[-1].file_id, 
                caption=message.caption or ""
            )
        elif message.video:
            await state.update_data(
                msg_type="video",
                video_id=message.video.file_id,
                caption=message.caption or ""
            )
        else:
            await message.answer("⚠️ Faqat matn, rasm yoki video xabar yuborishingiz mumkin.")
            return

        await state.set_state(BroadcastState.confirm)
        await message.answer(
            "❓ Xabarni barcha foydalanuvchilarga yuborishni tasdiqlaysizmi?",
            reply_markup=confirm_kb("broadcast_confirm")
        )
    except Exception as e:
        logger.exception("Error receiving broadcast message: %s", e)
        await message.answer("⚠️ Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")

# Confirm yes
@router.callback_query(BroadcastState.confirm, F.data == "broadcast_confirm_yes")
async def confirm_broadcast_yes(callback: CallbackQuery, state: FSMContext, session) -> None:
    status_msg = await callback.message.edit_text("⏳ Xabar yuborilmoqda. Iltimos, kuting...", reply_markup=None)
    try:
        data = await state.get_data()
        msg_type = data.get("msg_type")
        users = await get_all_users(session)
        
        success_count = 0
        fail_count = 0
        
        for user in users:
            try:
                if msg_type == "text":
                    await callback.bot.send_message(chat_id=user.telegram_id, text=data.get("content"))
                elif msg_type == "photo":
                    await callback.bot.send_photo(
                        chat_id=user.telegram_id, 
                        photo=data.get("photo_id"), 
                        caption=data.get("caption")
                    )
                elif msg_type == "video":
                    await callback.bot.send_video(
                        chat_id=user.telegram_id,
                        video=data.get("video_id"),
                        caption=data.get("caption")
                    )
                success_count += 1
            except Exception as send_err:
                logger.warning("Could not send broadcast to %s: %s", user.telegram_id, send_err)
                fail_count += 1
                
        await status_msg.answer(
            f"📢 Xabar barcha faol foydalanuvchilarga yuborildi!\n\n"
            f"✅ Muvaffaqiyatli: {success_count}\n"
            f"❌ Muvaffaqiyatsiz: {fail_count}",
            reply_markup=admin_menu_kb()
        )
        await status_msg.delete()
        await state.clear()
        await callback.answer()
    except Exception as e:
        logger.exception("Error confirming broadcast: %s", e)
        await callback.message.answer("⚠️ Xabarlarni yuborishda xatolik yuz berdi.", reply_markup=admin_menu_kb())
        await state.clear()

# Confirm no
@router.callback_query(BroadcastState.confirm, F.data == "broadcast_confirm_no")
async def confirm_broadcast_no(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        await state.clear()
        await callback.message.edit_text("❌ Xabar yuborish bekor qilindi.", reply_markup=None)
        await callback.message.answer("Bosh menyu:", reply_markup=admin_menu_kb())
        await callback.answer()
    except Exception as e:
        logger.exception("Error canceling broadcast: %s", e)
        await callback.message.answer("⚠️ Xatolik yuz berdi.", reply_markup=admin_menu_kb())
