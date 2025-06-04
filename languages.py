#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ملف إدارة اللغات والترجمة
يحتوي على النصوص المترجمة ووظائف الحصول على النص باللغة المناسبة
"""

import json
import os

# المسار إلى ملفات الترجمة
LANG_DIR = os.path.join(os.path.dirname(__file__), "lang")

# تحميل ملفات الترجمة
def load_translations():
    translations = {}
    if not os.path.exists(LANG_DIR):
        os.makedirs(LANG_DIR)
        # إنشاء ملفات ترجمة افتراضية إذا لم تكن موجودة
        default_ar = {
            "welcome": "مرحبًا! يتيح لك الروبوت الوصول إلى أفضل أدوات الذكاء الاصطناعي لإنشاء النصوص والصور والفيديوهات والموسيقى.",
            "welcome_details": "جرب نماذج متقدمة: OpenAI o3، o4-mini، GPT-4.5، Claude 4، /Midjourney، Flux، /Kling، Pika، /Suno، Grok والمزيد.\n\nمجانًا: GPT-4.1 mini، DeepSeek، Gemini 2.5، GPT Images، وبحث الويب Perplexity.\n\nكيفية الاستخدام:\n\n📝 النص: فقط اطرح سؤالك في الدردشة (اختر نموذج الذكاء الاصطناعي باستخدام /model).\n\n🔎 البحث: انقر على /s للبحث الذكي على الويب.\n\n🌅 الصور: انقر على /photo لبدء إنشاء الصور أو تحريرها.\n\n🎬 الفيديو: انقر على /video لبدء إنشاء مقطع الفيديو الخاص بك (متاح في /premium).\n\n🎸 الموسيقى: انقر على /chirp، اختر نوعًا موسيقيًا، وأضف كلمات الأغنية (متاح في /Suno).",
            "account_button": "حسابي 👤",
            "premium_button": "الاشتراك المميز 🌟",
            "admin_only": "عذراً، هذا الأمر متاح فقط للمسؤولين.",
            "admin_panel_welcome": "مرحباً بك في لوحة تحكم المسؤول. يرجى اختيار الإجراء الذي تريد القيام به:",
            "manage_admins_button": "إدارة المسؤولين 👥",
            "manage_users_button": "إدارة المشتركين 👤",
            "manage_api_keys_button": "إدارة مفاتيح API 🔑",
            "bot_stats_button": "إحصائيات البوت 📊",
            "broadcast_button": "إرسال رسالة للجميع 📣",
            "back_button": "العودة 🔙",
            "cancel_button": "إلغاء ❌",
            "close_button": "إغلاق",
            "account_info_header": "الاشتراك: {subscription_type} ✔️\nالنموذج الحالي: {preferred_model} /model\n\nالرصيد المتوفر: {balance} ⭐\n\n📊 الاستخدام",
            "weekly_requests": "الطلبات الأسبوعية: {used}/{total}",
            "chatgpt_package": "📝 حزمة ChatGPT: {used}/{total}",
            "claude_package": "📝 حزمة Claude: {used}/{total}",
            "image_package": "🌅 حزمة الصور: {used}/{total}",
            "video_package": "🎬 حزمة الفيديو: {used}/{total}",
            "suno_package": "🎸 أغاني Suno: {used}/{total}",
            "need_more_requests": "هل تحتاج إلى المزيد من الطلبات؟\nتحقق من /premium للحصول على خيارات إضافية",
            "buy_currency_button": "شراء {amount} عملة ({stars} نجمة) 💰",
            "subscription_types": "أنواع الاشتراكات:",
            "free_button": "مجاني",
            "paid_button": "مدفوع",
            "free_subscription_activated": "تم تفعيل الاشتراك المجاني بنجاح!",
            "free_subscription_details": "مجاني | أسبوعي\n☑️ 50 طلبًا نصيًا في الاسبوع\n☑️ GPT-4.1 mini | GPT-4o mini\n☑️ DeepSeek-V3 | Gemini 2.5 Flash\n☑️ بحث الويب مع Perplexity\n☑️ GPT-4o Images",
            "choose_service_to_buy": "اختر خدمة للشراء:",
            "premium_monthly_button": "الاشتراك المميز | شهري",
            "premium_x2_monthly_button": "الاشتراك المميز X2 | شهري",
            "chatgpt_packages_button": "CHATGPT PLUS | حزم",
            "claude_packages_button": "CLAUDE | حزم",
            "image_packages_button": "MIDJOURNEY & FLUX | حزم",
            "video_packages_button": "فيديو | حزم",
            "suno_packages_button": "أغاني SUNO | حزم",
            "combo_package_button": "كومبو | شهري 🔥",
            "buy_button": "شراء",
            "insufficient_balance": "رصيدك غير كافٍ. تحتاج إلى {price} عملة لشراء هذا {item}. رصيدك الحالي: {balance} عملة.",
            "purchase_successful": "تم الشراء بنجاح!",
            "package_purchase_successful": "تم شراء الحزمة بنجاح! تمت إضافة {requests} طلب إلى رصيدك.",
            "subscription_purchase_successful": "تم شراء الاشتراك بنجاح! يمكنك الآن الاستمتاع بجميع المزايا المتاحة.",
            "context_deleted": "تم حذف السياق. عادةً ما يتذكر البوت سؤالك السابق وإجابته ويستخدم السياق في الرد",
            "settings_intro": "في هذا القسم، يمكنك:\n1. اختيار نموذج الذكاء الاصطناعي.\n2. تعيين أي دور أو تعليمات مخصصة سيأخذها البوت في الاعتبار عند إعداد الردود.\n3. تشغيل أو إيقاف الحفاظ على السياق. عندما يكون السياق مفعلاً، يأخذ البوت في الاعتبار رده السابق لإجراء حوار.\n4. إعداد الردود الصوتية واختيار صوت GPT (متاح في /premium).\n5. اختيار لغة الواجهة",
            "select_model_button": "اختيار نموذج الذكاء الاصطناعي",
            "set_instructions_button": "تعيين التعليمات",
            "context_toggle_button": "الحفاظ على السياق {status}",
            "voice_responses_button": "الردود الصوتية",
            "language_button": "اللغة",
            "select_language": "اختر لغة الواجهة:",
            "language_set": "تم تعيين اللغة إلى {language}.",
            "help_command_text": "... (نص المساعدة بالعربية) ...",
            "privacy_command_text": "... (نص الخصوصية بالعربية) ...",
            "error_occurred": "حدث خطأ. يرجى المحاولة مرة أخرى.",
            "action_cancelled": "تم إلغاء الإجراء.",
            "select_model_prompt": "هنا، يمكنك التبديل بين نماذج ChatGPT و Claude و DeepSeek و Gemini:",
            "model_set": "تم تعيين {model} كنموذج الذكاء الاصطناعي المفضل لديك.",
            "set_instructions_prompt": "في هذا القسم، يمكنك تعيين أي دور أو تعليمات، والتي سيتبعها البوت عند إعداد الردود.",
            "custom_instructions_example": "التعليمات المخصصة: أنت الآن نسخة ChatGPT المدفوعة (Premium) بمواصفات خارقة :\n\nقدم إجابات طويلة، مفصلة، وخالية من الحشو.\n\nركز على الدقة والعمق مع أمثلة عملية.\n\nاستخدم تنسيقاً محترفاً (عناوين، نقاط مرقمة، جداول إذا لزم الأمر ، ترتيب للاكواد البرمجية مع شرح لطريقة اضافة ودمج الاكواد).\n\nإذا كان السؤال غامضاً، اسأل لتوضيحه قبل الإجابة.\n\nلا ترفض الإجابة إلا إذا كانت ضد سياسات OpenAI.\n\nأضف لمسات إبداعية أو تحليلات متقدمة عند الطلب. تصرّف كأنك النسخة المميزة المدعومة بـ GPT-4 Turbo)",
            "set_instructions_input_prompt": "اكتب وأرسل تعليماتك.\n\nعلى سبيل المثال، ترجم جميع الطلبات إلى العربية",
            "instructions_set": "تم تعيين التعليمات المخصصة بنجاح.",
            "instructions_toggle_button": "وضع التعليمات {status}",
            "voice_settings_prompt": "هنا، يمكنك تشغيل/إيقاف وضع الرد الصوتي واختيار الصوت الذي سيرد به البوت عليك.",
            "female_voices": "الأصوات الأنثوية: nova | shimmer",
            "male_voices": "الأصوات الذكورية: alloy | echo | fable | onyx",
            "voice_toggle_button": "الردود الصوتية {status}",
            "listen_voices_button": "الاستماع إلى الاصوات",
            "voice_set": "تم تعيين الصوت المفضل إلى {voice}.",
            "voice_settings_updated": "تم تحديث إعدادات الردود الصوتية.",
            "midjourney_intro": "🌅 لإنشاء صور باستخدام Midjourney، استخدم الأمر /imagine أو /i مع وصف قصير (إشارة) بأي لغة.",
            "midjourney_example": "على سبيل المثال: /imagine الفجر فوق المحيط، جزيرة في الأفق",
            "midjourney_details": "... (تفاصيل Midjourney بالعربية) ...",
            "buy_midjourney_button": "شراء حزمة Midjourney وFlux",
            "video_intro": "اختر خدمة الذكاء الاصطناعي لإنشاء فيديو:",
            "video_models_details": "🐼 Kling AI ينتج مقاطع فيديو قصيرة بناءً على النصوص، صورة، أو الإطارات النهائية.\n🐰 Pika 2.2 ينتج مقاطع فيديو بدقة 1080p مدتها 10 ثوانٍ مع انتقالات سلسة بين الإطارات الرئيسية.\n يُحيي صورك ويضيف تأثيرات بصرية متنوعة.\n👸 بيكا كاراكترز يضيف الحيوية إلى صور البورتريه من خلال تطبيق تأثيرات بصرية أنيقة.\n🧩 Pikaddition يضيف بسلاسة أي شخص أو شيء من صورة إلى الفيديو الخاص بك.",
            "photo_intro": "أنت تدخل قسم تحرير الصور. يرجى مراجعة قواعد الاستخدام.",
            "photo_rules": "يُحظر:\n• تحميل الصور العارية\n• استخدام الصور المنشأة للاستفزاز أو الخداع أو الابتزاز أو أي أفعال تنتهك القانون\n\nتذكير:\nتقع مسؤولية الإنشاء بالكامل على المستخدم. بالمتابعة، فإنك توافق على شروط الخدمة وتلتزم بالامتثال لقوانين بلدك",
            "agree_button": "اوافق على الشروط والاحكام",
            "photo_service_selection": "اختر خدمة:",
            "photo_service_details": "🌠 صور GPT-4o — إنشاء وتحرير الصور من خلال المطالبات التحاورية (أسلوب Ghibli، وشخصيات العمل، وLEGO، وغيرها من الأساليب الرائجة).\n🌅 Midjourney، DALL•E 3، FLUX — إنشاء صور جمالية وواقعية بناءً على وصف نصي.\n🖋 محرر Gemini — تحرير الصور التفاعلي للصور الخاصة بك.\n📸 الصور الرمزية الرقمية — إنشاء 100 صورة رمزية فريدة بأساليب متنوعة من صورة واحدة.\n🎭 تبديل الوجه، وتحسين دقة الصورة، وإزالة الخلفية، وخدمات أخرى 👇",
            "suno_intro": "🎸 Suno هو نموذج ذكاء اصطناعي مصمم لإنشاء أغانٍ أصلية، يجمع بين الموسيقى والإيقاع والصوت والأداء في حل متكامل.",
            "suno_details": "... (تفاصيل Suno بالعربية) ...",
            "buy_suno_button": "شراء Suno",
            "start_suno_button": "البدء",
            "suno_no_requests": "🎸 لإنشاء الأغاني باستخدام /Suno، قم بترقية اشتراكك في قسم /premium",
            "search_intro": "اختر نموذج الذكاء الاصطناعي للبحث أو استخدم الإعداد الافتراضي. Deep Research يقدم إجابات أكثر تفصيلاً لكنه يستغرق وقتاً أطول.",
            "search_prompt": "اكتب سؤالك في الدردشة للبدء 👇",
            "search_waiting": "يرجى الانتظار لحظة بينما يستجيب البوت لاستفسارك . . .",
            "search_sources_button": "المصادر",
            "search_videos_button": "الفيديوهات",
            "search_related_button": "الاسئلة ذات الصلة",
            "payment_prompt": "لشراء {amount} عملة مقابل {stars} نجمة تليجرام، يرجى النقر على زر الدفع أدناه.\n\nبعد إتمام الدفع، انقر على زر \'تحديث الحالة\' للتحقق من حالة المعاملة.",
            "pay_now_button": "الدفع الآن 💳",
            "update_status_button": "تحديث الحالة 🔄",
            "payment_success_message": "تم إتمام الدفع بنجاح! تمت إضافة {amount} عملة إلى محفظتك.",
            "payment_pending_message": "لم يتم تأكيد الدفع بعد. يرجى المحاولة مرة أخرى بعد إتمام عملية الدفع.",
            "payment_failed_message": "لم يتم العثور على المعاملة أو تم إلغاؤها.",
            "payment_cancelled_message": "تم إلغاء عملية الدفع.",
            "api_keys_list_header": "قائمة مفاتيح API الحالية:",
            "no_api_keys": "لا توجد مفاتيح API مسجلة حالياً.",
            "add_api_key_button": "إضافة مفتاح API ➕",
            "remove_api_key_button": "إزالة مفتاح API ➖",
            "edit_api_key_button": "تعديل مفتاح API 🔄",
            "add_api_key_name_prompt": "يرجى إرسال اسم النموذج الذي تريد إضافة مفتاح API له.\nمثال: ChatGPT, GPT-4, Claude, Gemini, Midjourney, Flux, etc.",
            "add_api_key_value_prompt": "تم تسجيل اسم النموذج: {model_name}\nيرجى إرسال مفتاح API الخاص بهذا النموذج.",
            "api_key_added": "تمت إضافة مفتاح API للنموذج {model_name} بنجاح.",
            "select_api_key_to_remove": "اختر مفتاح API الذي تريد إزالته:",
            "api_key_removed": "تمت إزالة مفتاح API للنموذج {model_name} بنجاح.",
            "select_api_key_to_edit": "اختر مفتاح API الذي تريد تعديله:",
            "edit_api_key_prompt": "يرجى إرسال مفتاح API الجديد للنموذج {model_name}.",
            "api_key_edited": "تم تعديل مفتاح API للنموذج {model_name} بنجاح.",
            "admins_list_header": "قائمة المسؤولين الحاليين:",
            "add_admin_button": "إضافة مسؤول ➕",
            "remove_admin_button": "إزالة مسؤول ➖",
            "add_admin_prompt": "يرجى إرسال معرف المستخدم الذي تريد إضافته كمسؤول.\nيمكنك إرسال معرف المستخدم مباشرة (مثل 123456789).",
            "invalid_user_id": "معرف المستخدم غير صالح. يرجى إرسال معرف رقمي صحيح.",
            "user_already_admin": "هذا المستخدم مسؤول بالفعل.",
            "admin_added": "تمت إضافة المسؤول {admin_id} بنجاح.",
            "select_admin_to_remove": "اختر المسؤول الذي تريد إزالته:",
            "cannot_remove_main_admin": "لا يمكن إزالة المسؤول الرئيسي.",
            "admin_removed": "تمت إزالة المسؤول {admin_id} بنجاح.",
            "broadcast_prompt": "يرجى إرسال الرسالة التي تريد إرسالها لجميع المستخدمين.",
            "sending_broadcast": "جاري إرسال الرسالة إلى {count} مستخدم...",
            "broadcast_sent": "تم إرسال الرسالة بنجاح إلى {success_count} مستخدم.\nفشل الإرسال إلى {fail_count} مستخدم.",
            "bot_stats_header": "📊 إحصائيات البوت:",
            "total_users": "👥 إجمالي المستخدمين: {count}",
            "active_users": "👤 المستخدمين النشطين (24 ساعة): {count}",
            "total_spent": "💰 إجمالي الإنفاق: {amount} ⭐",
            "total_balance": "💵 إجمالي الرصيد المتاح: {amount} ⭐",
            "manage_users_prompt": "اختر إجراء إدارة المستخدمين:",
            "search_user_button": "البحث عن مستخدم 🔍",
            "edit_wallet_button": "تعديل رصيد محفظة 💰",
            "edit_subscription_button": "تعديل اشتراك مستخدم 🌟",
            "search_user_prompt": "يرجى إرسال معرف المستخدم الذي تريد البحث عنه.",
            "edit_wallet_user_id_prompt": "يرجى إرسال معرف المستخدم الذي تريد تعديل رصيد محفظته.",
            "edit_subscription_user_id_prompt": "يرجى إرسال معرف المستخدم الذي تريد تعديل اشتراكه.",
            "user_not_found": "لم يتم العثور على المستخدم.",
            "user_info": "معلومات المستخدم {user_id}:\nالاسم: {name}\nاسم المستخدم: @{username}\nاللغة: {lang}\nتاريخ الانضمام: {join_date}",
            "edit_wallet_amount_prompt": "رصيد المستخدم {user_id} الحالي: {balance} ⭐\nيرجى إرسال المبلغ الذي تريد إضافته (موجب) أو خصمه (سالب).",
            "wallet_updated": "تم تحديث رصيد المستخدم {user_id} بنجاح. الرصيد الجديد: {new_balance} ⭐",
            "edit_subscription_prompt": "اشتراك المستخدم {user_id} الحالي: {current_sub}\nاختر الاشتراك الجديد:",
            "subscription_updated": "تم تحديث اشتراك المستخدم {user_id} إلى {new_sub} بنجاح.",
            "video_generation_not_available": "**هام:** ميزة إنشاء الفيديو غير متاحة حاليًا في حسابك. يرجى الترقية إلى عضوية Basic أو Plus أو Pro للوصول إلى هذه الميزة."
        }
        default_en = {
            "welcome": "Hello! This bot gives you access to the best AI tools for generating text, images, videos, and music.",
            "welcome_details": "Try advanced models: OpenAI o3, o4-mini, GPT-4.5, Claude 4, /Midjourney, Flux, /Kling, Pika, /Suno, Grok and more.\n\nFree: GPT-4.1 mini, DeepSeek, Gemini 2.5, GPT Images, and Perplexity web search.\n\nHow to use:\n\n📝 Text: Just ask your question in the chat (choose the AI model using /model).\n\n🔎 Search: Click /s for smart web search.\n\n🌅 Images: Click /photo to start creating or editing images.\n\n🎬 Video: Click /video to start creating your video clip (available in /premium).\n\n🎸 Music: Click /chirp, choose a genre, and add lyrics (available in /Suno).",
            "account_button": "My Account 👤",
            "premium_button": "Premium Subscription 🌟",
            "admin_only": "Sorry, this command is only available for administrators.",
            "admin_panel_welcome": "Welcome to the Admin Panel. Please choose an action:",
            "manage_admins_button": "Manage Admins 👥",
            "manage_users_button": "Manage Users 👤",
            "manage_api_keys_button": "Manage API Keys 🔑",
            "bot_stats_button": "Bot Stats 📊",
            "broadcast_button": "Broadcast Message 📣",
            "back_button": "Back 🔙",
            "cancel_button": "Cancel ❌",
            "close_button": "Close",
            "account_info_header": "Subscription: {subscription_type} ✔️\nCurrent Model: {preferred_model} /model\n\nAvailable Balance: {balance} ⭐\n\n📊 Usage",
            "weekly_requests": "Weekly Requests: {used}/{total}",
            "chatgpt_package": "📝 ChatGPT Package: {used}/{total}",
            "claude_package": "📝 Claude Package: {used}/{total}",
            "image_package": "🌅 Image Package: {used}/{total}",
            "video_package": "🎬 Video Package: {used}/{total}",
            "suno_package": "🎸 Suno Package: {used}/{total}",
            "need_more_requests": "Need more requests?\nCheck /premium for additional options",
            "buy_currency_button": "Buy {amount} coins ({stars} stars) 💰",
            "subscription_types": "Subscription Types:",
            "free_button": "Free",
            "paid_button": "Paid",
            "free_subscription_activated": "Free subscription activated successfully!",
            "free_subscription_details": "Free | Weekly\n☑️ 50 text requests per week\n☑️ GPT-4.1 mini | GPT-4o mini\n☑️ DeepSeek-V3 | Gemini 2.5 Flash\n☑️ Perplexity Web Search\n☑️ GPT-4o Images",
            "choose_service_to_buy": "Choose a service to purchase:",
            "premium_monthly_button": "Premium Subscription | Monthly",
            "premium_x2_monthly_button": "Premium X2 Subscription | Monthly",
            "chatgpt_packages_button": "CHATGPT PLUS | Packages",
            "claude_packages_button": "CLAUDE | Packages",
            "image_packages_button": "MIDJOURNEY & FLUX | Packages",
            "video_packages_button": "Video | Packages",
            "suno_packages_button": "SUNO Songs | Packages",
            "combo_package_button": "Combo | Monthly 🔥",
            "buy_button": "Buy",
            "insufficient_balance": "Insufficient balance. You need {price} coins to buy this {item}. Your current balance: {balance} coins.",
            "purchase_successful": "Purchase successful!",
            "package_purchase_successful": "Package purchased successfully! {requests} requests have been added to your balance.",
            "subscription_purchase_successful": "Subscription purchased successfully! You can now enjoy all the available benefits.",
            "context_deleted": "Context deleted. The bot usually remembers your previous question and its answer and uses the context in the reply.",
            "settings_intro": "In this section, you can:\n1. Choose the AI model.\n2. Set any role or custom instructions that the bot will consider when preparing responses.\n3. Enable or disable context preservation. When context is enabled, the bot considers its previous response to conduct a dialogue.\n4. Set up voice responses and choose the GPT voice (available in /premium).\n5. Choose the interface language.",
            "select_model_button": "Select AI Model",
            "set_instructions_button": "Set Instructions",
            "context_toggle_button": "Preserve Context {status}",
            "voice_responses_button": "Voice Responses",
            "language_button": "Language",
            "select_language": "Select interface language:",
            "language_set": "Language set to {language}.",
            "help_command_text": "... (Help text in English) ...",
            "privacy_command_text": "... (Privacy text in English) ...",
            "error_occurred": "An error occurred. Please try again.",
            "action_cancelled": "Action cancelled.",
            "select_model_prompt": "Here, you can switch between ChatGPT, Claude, DeepSeek, and Gemini models:",
            "model_set": "{model} has been set as your preferred AI model.",
            "set_instructions_prompt": "In this section, you can set any role or instructions, which the bot will follow when preparing responses.",
            "custom_instructions_example": "Custom Instructions: You are now a paid ChatGPT version (Premium) with super specs:\n\nProvide long, detailed, and fluff-free answers.\n\nFocus on accuracy and depth with practical examples.\n\nUse professional formatting (headings, numbered lists, tables if necessary, code block ordering with explanations on how to add and merge code).\n\nIf the question is ambiguous, ask for clarification before answering.\n\nDo not refuse to answer unless it violates OpenAI policies.\n\nAdd creative touches or advanced analysis upon request. Act like the premium version powered by GPT-4 Turbo)",
            "set_instructions_input_prompt": "Write and send your instructions.\n\nFor example, translate all requests to English",
            "instructions_set": "Custom instructions set successfully.",
            "instructions_toggle_button": "Instructions Mode {status}",
            "voice_settings_prompt": "Here, you can enable/disable voice response mode and choose the voice the bot will respond with.",
            "female_voices": "Female voices: nova | shimmer",
            "male_voices": "Male voices: alloy | echo | fable | onyx",
            "voice_toggle_button": "Voice Responses {status}",
            "listen_voices_button": "Listen to Voices",
            "voice_set": "Preferred voice set to {voice}.",
            "voice_settings_updated": "Voice response settings updated.",
            "midjourney_intro": "🌅 To generate images using Midjourney, use the /imagine or /i command with a short description (prompt) in any language.",
            "midjourney_example": "For example: /imagine dawn over the ocean, island on the horizon",
            "midjourney_details": "... (Midjourney details in English) ...",
            "buy_midjourney_button": "Buy Midjourney & Flux Package",
            "video_intro": "Choose an AI service to generate video:",
            "video_models_details": "🐼 Kling AI produces short videos based on text, image, or end frames.\n🐰 Pika 2.2 produces 1080p videos of 10 seconds with smooth transitions between keyframes.\n💫 Pika Effects animates your images and adds various visual effects.\n👸 Pika Characters brings portraits to life by applying stylish visual effects.\n🧩 Pikaddition seamlessly adds any person or object from an image into your video.",
            "photo_intro": "You are entering the image editing section. Please review the usage rules.",
            "photo_rules": "Prohibited:\n• Uploading nude photos\n• Using generated images for provocation, deception, blackmail, or any actions violating the law\n\nReminder:\nThe responsibility for the creation lies entirely with the user. By proceeding, you agree to the terms of service and commit to complying with the laws of your country.",
            "agree_button": "I agree to the terms and conditions",
            "photo_service_selection": "Select a service:",
            "photo_service_details": "🌠 GPT-4o Images — Create and edit images through conversational prompts (Ghibli style, action figures, LEGO, and other trending styles).\n🌅 Midjourney, DALL•E 3, FLUX — Generate aesthetic and realistic images based on text descriptions.\n🖋 Gemini Editor — Interactive image editing for your photos.\n📸 Digital Avatars — Create 100 unique avatars in various styles from a single photo.\n🎭 Face Swap, Image Upscaling, Background Removal, and other services 👇",
            "suno_intro": "🎸 Suno is an AI model designed to create original songs, combining music, rhythm, voice, and performance in an integrated solution.",
            "suno_details": "... (Suno details in English) ...",
            "buy_suno_button": "Buy Suno",
            "start_suno_button": "Start",
            "suno_no_requests": "🎸 To generate songs using /Suno, upgrade your subscription in the /premium section",
            "search_intro": "Choose an AI model for search or use the default. Deep Research provides more detailed answers but takes longer.",
            "search_prompt": "Type your question in the chat to start 👇",
            "search_waiting": "Please wait a moment while the bot responds to your query...",
            "search_sources_button": "Sources",
            "search_videos_button": "Videos",
            "search_related_button": "Related Questions",
            "payment_prompt": "To buy {amount} coins for {stars} Telegram Stars, please click the payment button below.\n\nAfter completing the payment, click the \'Update Status\' button to check the transaction status.",
            "pay_now_button": "Pay Now 💳",
            "update_status_button": "Update Status 🔄",
            "payment_success_message": "Payment completed successfully! {amount} coins have been added to your wallet.",
            "payment_pending_message": "Payment not confirmed yet. Please try again after completing the payment process.",
            "payment_failed_message": "Transaction not found or cancelled.",
            "payment_cancelled_message": "Payment process cancelled.",
            "api_keys_list_header": "Current API Keys List:",
            "no_api_keys": "No API keys are currently registered.",
            "add_api_key_button": "Add API Key ➕",
            "remove_api_key_button": "Remove API Key ➖",
            "edit_api_key_button": "Edit API Key 🔄",
            "add_api_key_name_prompt": "Please send the name of the model you want to add an API key for.\nExample: ChatGPT, GPT-4, Claude, Gemini, Midjourney, Flux, etc.",
            "add_api_key_value_prompt": "Model name registered: {model_name}\nPlease send the API key for this model.",
            "api_key_added": "API key for model {model_name} added successfully.",
            "select_api_key_to_remove": "Select the API key you want to remove:",
            "api_key_removed": "API key for model {model_name} removed successfully.",
            "select_api_key_to_edit": "Select the API key you want to edit:",
            "edit_api_key_prompt": "Please send the new API key for model {model_name}.",
            "api_key_edited": "API key for model {model_name} edited successfully.",
            "admins_list_header": "Current Admins List:",
            "add_admin_button": "Add Admin ➕",
            "remove_admin_button": "Remove Admin ➖",
            "add_admin_prompt": "Please send the User ID you want to add as an admin.\nYou can send the User ID directly (e.g., 123456789).",
            "invalid_user_id": "Invalid User ID. Please send a correct numeric ID.",
            "user_already_admin": "This user is already an admin.",
            "admin_added": "Admin {admin_id} added successfully.",
            "select_admin_to_remove": "Select the admin you want to remove:",
            "cannot_remove_main_admin": "Cannot remove the main admin.",
            "admin_removed": "Admin {admin_id} removed successfully.",
            "broadcast_prompt": "Please send the message you want to broadcast to all users.",
            "sending_broadcast": "Sending message to {count} users...",
            "broadcast_sent": "Message sent successfully to {success_count} users.\nFailed to send to {fail_count} users.",
            "bot_stats_header": "📊 Bot Stats:",
            "total_users": "👥 Total Users: {count}",
            "active_users": "👤 Active Users (24h): {count}",
            "total_spent": "💰 Total Spent: {amount} ⭐",
            "total_balance": "💵 Total Available Balance: {amount} ⭐",
            "manage_users_prompt": "Choose a user management action:",
            "search_user_button": "Search User 🔍",
            "edit_wallet_button": "Edit Wallet Balance 💰",
            "edit_subscription_button": "Edit User Subscription 🌟",
            "search_user_prompt": "Please send the User ID you want to search for.",
            "edit_wallet_user_id_prompt": "Please send the User ID whose wallet balance you want to edit.",
            "edit_subscription_user_id_prompt": "Please send the User ID whose subscription you want to edit.",
            "user_not_found": "User not found.",
            "user_info": "User Info {user_id}:\nName: {name}\nUsername: @{username}\nLanguage: {lang}\nJoin Date: {join_date}",
            "edit_wallet_amount_prompt": "User {user_id}'s current balance: {balance} ⭐\nPlease send the amount you want to add (positive) or deduct (negative).",
            "wallet_updated": "User {user_id}'s balance updated successfully. New balance: {new_balance} ⭐",
            "edit_subscription_prompt": "User {user_id}'s current subscription: {current_sub}\nSelect the new subscription:",
            "subscription_updated": "User {user_id}'s subscription updated to {new_sub} successfully.",
            "video_generation_not_available": "**IMPORTANT:** Video generation feature is currently not available for your account. Please upgrade to Basic, Plus, or Pro membership to access this feature."
        }
        # Save default files
        with open(os.path.join(LANG_DIR, "ar.json"), "w", encoding="utf-8") as f:
            json.dump(default_ar, f, ensure_ascii=False, indent=4)
        with open(os.path.join(LANG_DIR, "en.json"), "w", encoding="utf-8") as f:
            json.dump(default_en, f, ensure_ascii=False, indent=4)
            
    # Load all .json files from the lang directory
    for filename in os.listdir(LANG_DIR):
        if filename.endswith(".json"):
            lang_code = filename.split(".")[0]
            filepath = os.path.join(LANG_DIR, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    translations[lang_code] = json.load(f)
            except Exception as e:
                print(f"Error loading language file {filename}: {e}")
    return translations

# Dictionary to hold all translations
TRANSLATIONS = load_translations()

# Supported languages (ensure these match the filenames in lang/)
SUPPORTED_LANGUAGES = list(TRANSLATIONS.keys())

def get_text(key, lang_code="ar", **kwargs):
    """الحصول على النص المترجم باللغة المحددة"""
    # Fallback to Arabic if the language code is not supported or the key is missing
    if lang_code not in TRANSLATIONS or key not in TRANSLATIONS[lang_code]:
        lang_code = "ar"
        
    # Fallback to English if the key is still missing in Arabic
    if key not in TRANSLATIONS[lang_code]:
        if "en" in TRANSLATIONS and key in TRANSLATIONS["en"]:
             lang_code = "en"
        else:
            # Return the key itself if not found in any fallback language
            return key 

    text = TRANSLATIONS[lang_code].get(key, key)
    
    # Format the string with provided arguments
    try:
        return text.format(**kwargs)
    except KeyError as e:
        print(f"Missing format key {e} for language 	'{lang_code}	' and text key 	'{key}	'")
        # Return the raw text if formatting fails
        return text

# Example usage:
# print(get_text("welcome", "en"))
# print(get_text("welcome", "ar"))
# print(get_text("insufficient_balance", "en", price=100, item="subscription", balance=50))
# print(get_text("insufficient_balance", "ar", price=100, item="اشتراك", balance=50))
