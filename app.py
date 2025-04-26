import streamlit as st
import pandas as pd
import json
import os
import time
import pytz
from datetime import datetime, date, timedelta
from streamlit_autorefresh import st_autorefresh



# ضبط الوقت على المنطقة الزمنية الخاصة بك (UTC+3)
tz = pytz.timezone('Asia/Riyadh')  # الرياض
current_time = datetime.now(tz)




# إعداد صفحة Streamlit
st.set_page_config(
    page_title="تطبيق إدارة اليومية",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.sidebar.image("logo.png", use_container_width=True)

# تنسيقات CSS مخصصة لواجهة فخمة
st.markdown(
    """
    <style>
    /* خلفية الشريط الجانبي */
    .sidebar .sidebar-content {
        background-image: linear-gradient(135deg, #2E86C1 0%, #2874A6 100%);
        color: #FFFFFF;
    }
    .sidebar .sidebar-content .stRadio > label,
    .sidebar .sidebar-content .stSelectbox > div {
        color: #FFFFFF;
    }
    /* بطاقات المحتوى */
    .stApp > div:nth-child(1) > div > div > div {
        background-color: #FDFEFE !important;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    /* أزرار */
    .stButton>button {
        background-color: #2E86C1;
        color: #FFFFFF;
        border-radius: 8px;
        padding: 10px 20px;
    }
    .stButton>button:hover {
        background-color: #1B4F72;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# الرمز السري ومصادقة المستخدم
SECRET_CODE = "1111"
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 أدخل الرمز السري")
    pwd = st.text_input("الرمز السري:", type="password")
    if pwd:
        if pwd == SECRET_CODE:
            st.session_state.authenticated = True
            st.success("✅ تم التحقق بنجاح")
            # حاول إعادة تشغيل السكريبت إذا كانت الوظيفة متاحة
            try:
                st.rerun()
            except Exception:
                pass
        else:
            st.error("❌ الرمز غير صحيح")
    # إذا لم يتم التحقق، أوقف التنفيذ بعد عرض الإدخال أو الخطأ
    if not st.session_state.authenticated:
        st.stop()

# إعداد الشريط الجانبي
st.sidebar.title("📋 الأقسام")
page = st.sidebar.radio("انتقل إلى:", [
    "الصفحة الرئيسية", "الجدول اليومي", "فيديوهات التمارين", "أذكار", "جدول القرآن","افكاري","مهام آجلة"
])

@st.cache_data(show_spinner=False)# إضافة show_spinner=False لإخفاء رسالة التخزين المؤقت
def load_completed_tasks(file_name, today):
    """دالة لتحميل المهام المكتملة مع معالجة الأخطاء"""
    if not os.path.exists(file_name):
        return set()
    
    try:
        df = pd.read_csv(file_name, encoding='utf-8-sig')
        df['تاريخ'] = pd.to_datetime(df['تاريخ']).dt.date
        completed = set(df[(df['تاريخ'] == today) & (df['الحالة'] == 'مكتمل')]['المهمة'])
        return completed
    except Exception as e:
        st.error(f"خطأ في قراءة ملف المهام: {str(e)}")
        return set()

# الصفحة الرئيسية
def home_page():
    st_autorefresh(interval=1000, key="refresh")

    col1, col2 = st.columns([2, 3])

    with col1:
        st.title("مرحبًا بك احمد   ")
        st.markdown("---")
        st.metric("📅 التاريخ", current_time.strftime('%Y-%m-%d'))
        st.metric("⏰ الوقت الآن", current_time.strftime("%I:%M:%S %p"))


    # 👇 المهام تبدأ هنا مباشرة بعد الوقت

        current_hour = datetime.now().hour
        if 4 <= current_hour < 12:
            period_name = "🌅 الصباح"
        elif 12 <= current_hour < 16:
            period_name = "🌞 الظهر"
        elif 16 <= current_hour < 19:
            period_name = "🏋️ العصر"
        else:
            period_name = "🌙 من المغرب حتى النوم"

        if period_name:
            st.markdown("---")
            st.subheader(f"مهام {period_name.split()[-1]}")

            tasks = get_daily_tasks()
            file_name = "daily_tasks.csv"
            today = date.today()

            completed_tasks = load_completed_tasks(file_name, today)

            with st.container():
                for task in tasks.get(period_name, []):
                    task_key = f"{period_name}_{task}_{today}"
                    cols = st.columns([4, 1])
                    with cols[0]:
                        if task in completed_tasks:
                            st.markdown(f"<p style='margin-bottom: 5px; color:green'><del>- {task}</del> (مكتمل)</p>",unsafe_allow_html=True)
                        else:
                            st.markdown(f"<p style='margin-bottom: 5px'>- {task}</p>",unsafe_allow_html=True)
                    with cols[1]:
                        if st.button("✔️ إنجاز" if task not in completed_tasks else "↩️ إلغاء", key=task_key):
                            new_status = "مكتمل" if task not in completed_tasks else "غير مكتمل"
                            update_task_status(task, today, new_status)
                            st.cache_data.clear()
                            st.rerun()

            # ✅ مهام اليوم
            st.markdown("---")
            st.subheader("📌 مهام اليوم")

            tasks_file = "future_tasks.json"
            today_str = date.today().strftime("%Y-%m-%d")

            try:
                if os.path.exists(tasks_file):
                    with open(tasks_file, "r", encoding="utf-8") as f:
                        tasks = json.load(f)
                        today_tasks = [task for task in tasks if task["date"] == today_str and not task["completed"]]

                        if today_tasks:
                            for task in today_tasks:
                                col_task, col_status = st.columns([4, 1])
                                with col_task:
                                    st.markdown(f"**{task['task']}**")
                                with col_status:
                                    if st.button("✔️", key=f"complete_{task['task']}"):
                                        for t in tasks:
                                            if t["task"] == task["task"] and t["date"] == task["date"]:
                                                t["completed"] = True
                                        with open(tasks_file, "w", encoding="utf-8") as f:
                                            json.dump(tasks, f, ensure_ascii=False, indent=4)
                                        st.rerun()
                        else:
                            st.info("لا توجد مهام محددة لهذا اليوم")
            except Exception as e:
                st.warning(f"حدث خطأ أثناء تحميل المهام: {e}")

    # 👇 أخيرًا: عرض الصورة بعد المهام
    with col2:
        if os.path.exists("me.png"):
            st.image("me.png", use_container_width=True)


# هذه الدالة الجديدة نضيفها قبل daily_schedule_page
def get_daily_tasks():
    """ترجع المهام مجمعة حسب الفترات الزمنية"""
    return {
        "🌅 الصباح": [
            "الفجر في المسجد", "فرش الأسنان وغسل الوجه", "أذكار الصباح", "Cordyceps على الريق",
            "مراجعة جزء من القرآن", "فطور + ALCAR", "دورة Python (1 ساعة)", "تدريب طباعة أو تحسين الخط"
        ],
        "🌞 الظهر": [
            "صلاة الظهر في المسجد", "دورة SQL (30–45 دقيقة)", "PowerShell / اختصارات (15 دقيقة)",
            "غداء + Resveratrol", "دورة Excel + Power BI (1 ساعة)"
        ],
        "🏋️ العصر": [
            "صلاة العصر في المسجد", "التمرين حسب الجدول", "تغذية بعد التمرين", "دوش"
        ],
        "🌙 من المغرب حتى النوم": [
            "صلاة المغرب والعشاء في المسجد", "أذكار المساء", "إكمال النواقص", "Magnesium + عصير حبحب",
            "الوتر + ورد + أدعية", "فرش الأسنان وغسل الوجه", "قراءة سورة الملك"
        ]
    }


def daily_schedule_page():
    st.title("📅 الجدول اليومي")
    selected_date = st.date_input("📅 اختر التاريخ:", date.today())
    today = pd.to_datetime(selected_date).date()
    
    tasks = get_daily_tasks()
    file_name = "daily_tasks.csv"
    
    # تحميل البيانات
    if os.path.exists(file_name):
        try:
            df = pd.read_csv(file_name, encoding='utf-8-sig')
            df['تاريخ'] = pd.to_datetime(df['تاريخ']).dt.date
        except:
            df = pd.DataFrame(columns=["تاريخ", "المهمة", "الحالة"])
    else:
        df = pd.DataFrame(columns=["تاريخ", "المهمة", "الحالة"])
    
    # معالجة المهام
    completed = 0
    total = sum(len(v) for v in tasks.values())
    
    for section, items in tasks.items():
        st.subheader(section)
        for idx, task in enumerate(items):
            # التحقق من حالة المهمة
            is_completed = not df[(df['تاريخ'] == today) & 
                                (df['المهمة'] == task) & 
                                (df['الحالة'] == 'مكتمل')].empty
            
            # عرض المهمة مع checkbox
            cols = st.columns([4, 1])
            with cols[0]:
                if is_completed:
                    st.markdown(f"<span style='color:green'><del>{task}</del></span>", 
                               unsafe_allow_html=True)
                else:
                    st.markdown(task)
            
            with cols[1]:
                new_status = st.checkbox(
                    "مكتمل", 
                    value=is_completed, 
                    key=f"daily_{task}_{today}_{idx}"
                )
            
            # تحديث حالة المهمة
            df = df[~((df['تاريخ'] == today) & (df['المهمة'] == task))]
            df = pd.concat([
                df,
                pd.DataFrame([[today, task, 'مكتمل' if new_status else 'غير مكتمل']],
                           columns=df.columns)
            ], ignore_index=True)
            
            if new_status:
                completed += 1
    
    # حفظ البيانات
    df.to_csv(file_name, index=False, encoding='utf-8-sig')
    
    # عرض الإحصائيات
    st.markdown("---")
    st.success(f"✅ أنجزت {completed} من {total} مهمة — {int((completed/total)*100)}%")
    if st.button("🔄 تحديث الصفحة"):
        st.rerun()

def update_task_status(task, date, status):
    try:
        file_name = "daily_tasks.csv"
        
        # إنشاء DataFrame جديد إذا لم يكن الملف موجوداً
        if not os.path.exists(file_name):
            df = pd.DataFrame(columns=["تاريخ", "المهمة", "الحالة"])
        else:
            df = pd.read_csv(file_name, encoding='utf-8-sig')
            df['تاريخ'] = pd.to_datetime(df['تاريخ']).dt.date
        
        # إزالة أي إدخالات قديمة لنفس المهمة والتاريخ
        df = df[~((df['تاريخ'] == date) & (df['المهمة'] == task))]
        
        # إضافة الإدخال الجديد
        new_row = pd.DataFrame([{
            "تاريخ": date,
            "المهمة": task,
            "الحالة": status
        }])
        
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(file_name, index=False, encoding='utf-8-sig')
        
    except Exception as e:
        st.error(f"حدث خطأ أثناء تحديث المهمة: {str(e)}")


def show_today_special_tasks():
    tasks_file = "future_tasks.json"
    today_str = date.today().strftime("%Y-%m-%d")
    
    try:
        if os.path.exists(tasks_file):
            with open(tasks_file, "r", encoding="utf-8") as f:
                tasks = json.load(f)
                today_tasks = [t for t in tasks if t["date"] == today_str and not t["completed"]]
                
                if today_tasks:
                    for task in today_tasks:
                        cols = st.columns([4, 1])
                        with cols[0]:
                            st.markdown(f"**{task['task']}**")
                        with cols[1]:
                            if st.button("✔️", key=f"complete_special_{task['task']}"):
                                update_special_task(task['task'], today_str)
                else:
                    st.info("لا توجد مهام خاصة لهذا اليوم")
    except Exception as e:
        st.warning(f"حدث خطأ أثناء تحميل المهام: {e}")

def update_special_task(task, date):
    tasks_file = "future_tasks.json"
    try:
        with open(tasks_file, "r", encoding="utf-8") as f:
            tasks = json.load(f)
        
        for t in tasks:
            if t["task"] == task and t["date"] == date:
                t["completed"] = True
        
        with open(tasks_file, "w", encoding="utf-8") as f:
            json.dump(tasks, f, ensure_ascii=False, indent=4)
        st.rerun()
    except Exception as e:
        st.error(f"خطأ في تحديث المهمة: {str(e)}")

# صفحة فيديوهات التمارين
def workout_videos_page():
    st.title("🎥 فيديوهات التمارين")
    st.markdown("### اختر يوم التمرين:")
    days = {
        "اليوم الأول": [
            ("تمارين المرونة", "https://www.youtube.com/watch?v=y-N9T1DUvbk&ab_channel=SHMSHONMOON"),
            ("تمرين مفصل القدم", "https://www.youtube.com/watch?v=f9Lc3x8zLR8"),
            ("تمارين اللياقة", "https://www.youtube.com/watch?v=qJ7eOpJtYmg"),
            ("تمارين الكتف", "https://www.youtube.com/watch?v=mvBUuhinalo"),
            ("تمارين الصدر", "https://www.youtube.com/watch?v=D2kq3I7diuE")
        ],
        "اليوم الثاني": [
            ("تمارين المرونة", "https://www.youtube.com/watch?v=y-N9T1DUvbk&ab_channel=SHMSHONMOON"),
            ("تمارين اللياقة", "https://www.youtube.com/watch?v=W431mrJarDs"),
            ("تمارين البطن", "https://www.youtube.com/watch?v=fjZ6rgtyTSM"),
            ("تمارين الذراع", "https://www.youtube.com/watch?v=Ea2fEvR5ii0")
        ],
        "اليوم الثالث": [
            ("تمارين المرونة", "https://www.youtube.com/watch?v=y-N9T1DUvbk&ab_channel=SHMSHONMOON"),
            ("تمارين مرونة الحوض", "https://www.youtube.com/watch?v=zCurzz7Ir2Q&ab_channel=A_BOOM"),
            ("تمرين مفصل القدم", "https://www.youtube.com/watch?v=f9Lc3x8zLR8"),
            ("تمارين الظهر", "https://www.youtube.com/watch?v=lZ-WUS--018"),
            ("تمارين الأرجل", "https://www.youtube.com/watch?v=أرجل3")
        ],
        "اليوم الرابع": [
            ("تمارين المرونة", "https://www.youtube.com/watch?v=y-N9T1DUvbk&ab_channel=SHMSHONMOON"),
            ("تمارين اللياقة", "https://www.youtube.com/watch?v=lyB4XoGIWPA"),
            ("تمرين مفصل القدم", "https://www.youtube.com/watch?v=f9Lc3x8zLR8"),
            ("تمارين الكور", "https://www.youtube.com/watch?v=4m-esy408eQ")
        ],
        "اليوم الخامس": [
            ("تمارين المرونة", "https://www.youtube.com/watch?v=y-N9T1DUvbk&ab_channel=SHMSHONMOON"),
            ("تمارين مرونة الحوض","https://www.youtube.com/watch?v=zCurzz7Ir2Q&ab_channel=A_BOOM"),
            ("تمارين اللياقة", "https://www.youtube.com/watch?v=PTZNYScvKrY"),
            ("تمارين الكور", "https://www.youtube.com/watch?v=-fq72QfRhTk")
        ],
    }
    sel = st.selectbox("اختر اليوم:", list(days.keys()))
    key = f"vid_{sel}"
    if key not in st.session_state:
        st.session_state[key] = 0
    
    vids = days[sel]
    idx = st.session_state[key]
    
    # ─── وضع التايمر فوق الفيديو مباشرة ───
    timer_col, video_col = st.columns([1, 2])  # تقسيم العمودين
    
    with timer_col:
        st.markdown("### ⏱️ العد التنازلي")
        timer_duration = st.slider(
            "المدة (ثواني):",
            min_value=5,
            max_value=300,
            value=30,
            step=5,
            key=f"timer_{sel}_{idx}"  # مفتاح فريد لكل فيديو
          
        )
        
        if st.button("▶️ تشغيل", key=f"start_{sel}_{idx}"):
            end_time = datetime.now() + timedelta(seconds=timer_duration)
            timer_placeholder = st.empty()
            progress_bar = st.progress(0)
            
            while datetime.now() < end_time:
                remaining = (end_time - datetime.now()).total_seconds()
                mins, secs = divmod(int(remaining), 60)
                timer_placeholder.markdown(f"### ⏳ `{mins:02d}:{secs:02d}`")
                progress_bar.progress(1 - (remaining / timer_duration))
                time.sleep(0.1)
            
            timer_placeholder.markdown("### ✅ تم الانتهاء!")
            progress_bar.empty()


        
            # تشغيل الصوت تلقائيًا باستخدام HTML
            audio_html = """
            <audio autoplay>
                <source src="https://assets.mixkit.co/sfx/preview/mixkit-bell-notification-933.mp3" type="audio/mp3">
            </audio>
            """
            st.markdown(audio_html, unsafe_allow_html=True)

        
    with video_col:
        st.markdown(f"**{vids[idx][0]}**")
        st.video(vids[idx][1])
    
    # ─── أزرار التنقل ───
    col1, col2 = st.columns(2)
    with col1:
        if idx > 0:
            st.button("⬅️ السابق", on_click=lambda: st.session_state.__setitem__(key, idx - 1))
    with col2:
        if idx < len(vids) - 1:
            st.button("التالي ➡️", on_click=lambda: st.session_state.__setitem__(key, idx + 1))
    
    st.markdown(f"### الفيديو {idx + 1} من {len(vids)}")


# صفحة الأذكار

def azkark_page():
    st.title("🕌 أذكارك")
    options = ["اذكار الصباح","اذكار المساء","اذكار النوم"]
    sel = st.selectbox("اختر الذكر:", options)
    st.markdown("---")
    if sel == "اذكار الصباح":
        st.write(" افتح تطبيق اذكار ")
    elif sel == "اذكار المساء":
        st.write(" افتح تطبيق اذكار ")
    else:
        st.write(" افتح تطبيق اذكار ")

# صفحة جدول القرآن

def quran_schedule_page():
    st.title("📖 جدول الحفظ والمراجعة")
    schedule = [
        ("1", "المائدة (1-2)", "عم"),
        ("2", "ـــــ (3-4)", "تبارك + المائدة (1-4)"),
        ("3", "ـــــ (5-6)", "المجادلة + المائدة (1-6)"),
        ("4", "ـــــ (7-8)", "نصف جزء الذاريات + المائدة (1-8)"),
        ("5", "ـــــ (9-10)", "نصف جزء الذاريات + المائدة (1-10)"),
        ("6", "ـــــ (11-12)", "نصف جزء الاحقاف + المائدة (1-12)"),
        ("7", "ـــــ (13-14)", "نصف جزء الاحقاف + المائدة (3-14)"),
        ("8", "ـــــ (15-16)", "الجاثية – الدخان + المائدة (5-16)"),
        ("9", "ـــــ (17-18)", "الزخرف + المائدة (7-18)"),
        ("10", "ـــــ (19-20)", "الشورى + المائدة (9-20)"),
        ("11", "ـــــ (21-22)", "فصلت + المائدة (11-22)"),
        ("12", "الأنعام (1-2)", "غافر + المائدة (13-22)"),
        ("13", "ـــــ (3-4)", "الزمر + الأنعام (1-4) + المائدة (15-22)"),
        ("14", "ـــــ (5-6)", "ص – يس + الأنعام (1-6) + المائدة (17-22)"),
        ("15", "ـــــ (7-8)", "فاطر + الأنعام (1-8) + المائدة (19-22)"),
        ("16", "ـــــ (9-10)", "سبأ + الأنعام (1-10) + المائدة (21-22)"),
        ("17", "ـــــ (11-12)", "الأحزاب + الأنعام (1-12)"),
        ("18", "ـــــ (13-14)", "السجدة – لقمان + الأنعام (3-14)"),
        ("19", "ـــــ (15-16)", "الروم + الأنعام (5-16)"),
        ("20", "ـــــ (17-18)", "العنكبوت + الأنعام (7-18)"),
        ("21", "ـــــ (19-20)", "القصص + الأنعام (9-20)"),
        ("22", "ـــــ (21-23)", "النمل + الأنعام (11-23)"),
        ("23", "الأعراف (1-2)", "الشعراء + الأنعام (13-23)"),
        ("24", "ـــــ (3-4)", "الفرقان + الأعراف (1-4) + الأنعام (15-23)"),
        ("25", "ـــــ (5-6)", "النور + الأعراف (1-6) + الأنعام (17-23)"),
        ("26", "ـــــ (7-8)", "المؤمنون + الأعراف (1-8) + الأنعام (19-23)"),
        ("27", "ـــــ (9-10)", "الحج + الأعراف (1-10) + الأنعام (21-23)"),
        ("28", "ـــــ (11-12)", "الأنبياء + الأعراف (1-12)"),
        ("29", "الأعراف (13-14)", "طه – مريم + الأعراف (3-14)"),
        ("30", "ـــــ (15-16)", "الكهف – الإسراء + الأعراف (5-16)"),
        ("31", "ـــــ (17-18)", "نص النحل + الأعراف (7-18)"),
        ("32", "ـــــ (19-20)", "نص النحل + الأعراف (9-20)"),
        ("33", "ـــــ (21-22)", "الحجر – إبراهيم + الأعراف (11-22)"),
        ("34", "ـــــ (23-24)", "الرعد – يوسف + الأعراف (13-24)"),
        ("35", "ـــــ (25-26)", "نصف هود + الأعراف (15-26)"),
        ("36", "الأنفال (1-2)", "نصف هود + الأعراف (17-26)"),
        ("37", "ـــــ (3-4)", "نصف يونس + الأنفال (1-4) + الأعراف (19-26)"),
        ("38", "ـــــ (5-6)", "نصف يونس + الأنفال (1-6) + الأعراف (21-26)"),
        ("39", "ـــــ (7-8)", "ثلث المائدة + الأنفال (1-8) + الأعراف (23-26)"),
        ("40", "ـــــ (9-10)", "ثلث المائدة + الأنفال (1-10) + الأعراف (23-26)"),
        ("41", "التوبة (1-2)", "ثلث المائدة + الأنفال (1-10)"),
        ("42", "ـــــ (3-4)", "ثلث الأنعام + التوبة (1-4) + الأنفال (3-10)"),
        ("43", "ـــــ (5-6)", "ثلث الأنعام + التوبة (1-6) + الأنفال (5-10)"),
        ("44", "ـــــ (7-8)", "ثلث الأنعام + التوبة (1-8) + الأنفال (7-10)"),
        ("45", "ـــــ (9-10)", "ثلث الأعراف + التوبة (1-10) + الأنفال (9-10)"),
        ("46", "ـــــ (11-12)", "ثلث الأعراف + التوبة (1-12)"),
        ("47", "ـــــ (13-14)", "ثلث الأعراف + التوبة (3-14)"),
        ("48", "ـــــ (15-16)", "نصف الأنفال + التوبة (5-16)"),
        ("49", "ـــــ (17-18)", "نصف الأنفال + التوبة (7-18)"),
        ("50", "ـــــ (19-21)", "ثلث التوبة + التوبة (9-21)"),
        ("51", "ـــــــــــــــ", "التوبة (11-21)"),
        ("52", "ــــــــــــــــ", "التوبة (13-21)"),
        ("53", "ــــــــــــــــ", "ثلث التوبة + التوبة (15-21)"),
        ("54", "ــــــــــــــــ", "التوبة (17-21)"),
        ("55", "ــــــــــــــــ", "ثلث التوبة + التوبة (19-21)"),
    ]
    df_sched = pd.DataFrame(schedule, columns=["اليوم","الحفظ","المراجعة"])
    save_file = "quran_review.csv"
    if not os.path.exists(save_file):
        pd.DataFrame(columns=["التاريخ","اليوم","الحفظ","المراجعة","الحالة"]).to_csv(save_file, index=False, encoding='utf-8-sig')
    review_df = pd.read_csv(save_file, encoding='utf-8-sig')
    review_df["اليوم"] = review_df["اليوم"].astype(str)
    selected_date = st.date_input("📅 اختر تاريخ التسميع", value=date.today())
    opt = [f"{r['اليوم']} - حفظ: {r['الحفظ']} | مراجعة: {r['المراجعة']}" for _,r in df_sched.iterrows()]
    sel = st.selectbox("اختر اليوم:", opt)
    day = sel.split(" - ")[0]
    row = df_sched[df_sched["اليوم"]==day].iloc[0]
    marked = st.checkbox("تم التسميع لهذا اليوم")
    if st.button("💾 حفظ التسميع"):
        review_df = review_df[review_df["اليوم"]!=day]
        new = {"التاريخ": selected_date.strftime("%Y-%m-%d"), "اليوم": day,
               "الحفظ": row["الحفظ"], "المراجعة": row["المراجعة"],
               "الحالة": "✔️" if marked else "❌"}
        review_df = pd.concat([review_df, pd.DataFrame([new])], ignore_index=True)
        review_df.to_csv(save_file, index=False, encoding='utf-8-sig')
        st.success("✅ تم حفظ التسميع.")
    merged = df_sched.merge(review_df[["اليوم","التاريخ","الحالة"]], on="اليوم", how="left")
    merged["تم التسميع"] = merged["الحالة"].apply(lambda x: "✔️" if x=="✔️" else "")
    merged["تاريخ التسميع"] = merged["التاريخ"].fillna("")
    st.markdown("---")
    st.dataframe(merged[["اليوم","الحفظ","المراجعة","تم التسميع","تاريخ التسميع"]], use_container_width=True)

def ideas_page():
    st.title("💡 أفكاري")
    st.markdown("مكان لحفظ أفكارك وتعديلها لاحقًا")
    
    # تحميل الأفكار المسبقة إذا وجدت
    ideas_file = "my_ideas.json"
    ideas = {}  # تهيئة القاموس فارغاً
    
    # معالجة حالة الملف غير موجود أو فارغ
    try:
        if os.path.exists(ideas_file):
            with open(ideas_file, "r", encoding="utf-8") as f:
                file_content = f.read()
                if file_content.strip():  # التأكد من أن الملف ليس فارغاً
                    ideas = json.loads(file_content)
                else:
                    ideas = {}
    except json.JSONDecodeError:
        st.warning("⚠️ حدث خطأ في قراءة ملف الأفكار، سيتم إنشاء ملف جديد")
        ideas = {}
    
    # قسم إضافة/تعديل الفكرة
    st.subheader("أضف/عدل فكرة")
    idea_title = st.text_input("عنوان الفكرة:")
    idea_content = st.text_area("نص الفكرة:", height=200)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 حفظ الفكرة"):
            if idea_title and idea_content:
                ideas[idea_title] = idea_content
                try:
                    with open(ideas_file, "w", encoding="utf-8") as f:
                        json.dump(ideas, f, ensure_ascii=False, indent=4)
                    st.success("تم حفظ الفكرة بنجاح!")
                except Exception as e:
                    st.error(f"حدث خطأ أثناء الحفظ: {e}")
            else:
                st.warning("الرجاء إدخال عنوان ونص الفكرة")
    
    with col2:
        if st.button("🗑️ مسح جميع الأفكار"):
            ideas = {}
            try:
                with open(ideas_file, "w", encoding="utf-8") as f:
                    json.dump(ideas, f, ensure_ascii=False, indent=4)
                st.success("تم مسح جميع الأفكار")
            except Exception as e:
                st.error(f"حدث خطأ أثناء المسح: {e}")
    
    st.markdown("---")
    
    # قسم عرض الأفكار
    st.subheader("أفكارك المحفوظة")
    if not ideas:
        st.info("لا توجد أفكار محفوظة بعد")
    else:
        selected_idea = st.selectbox("اختر فكرة لعرضها:", list(ideas.keys()))
        st.markdown(f"**{selected_idea}**")
        st.write(ideas[selected_idea])
        
        if st.button("✏️ تعديل هذه الفكرة"):
            if idea_title and idea_content:
                # حذف القديم إذا تغير العنوان
                if selected_idea != idea_title:
                    del ideas[selected_idea]
                ideas[idea_title] = idea_content
                try:
                    with open(ideas_file, "w", encoding="utf-8") as f:
                        json.dump(ideas, f, ensure_ascii=False, indent=4)
                    st.success("تم تحديث الفكرة!")
                except Exception as e:
                    st.error(f"حدث خطأ أثناء التعديل: {e}")
            else:
                st.warning("الرجاء إدخال عنوان ونص الفكرة أولاً")
        
        if st.button("❌ حذف هذه الفكرة"):
            del ideas[selected_idea]
            try:
                with open(ideas_file, "w", encoding="utf-8") as f:
                    json.dump(ideas, f, ensure_ascii=False, indent=4)
                st.success("تم حذف الفكرة!")
            except Exception as e:
                st.error(f"حدث خطأ أثناء الحذف: {e}")
            # إعادة تحميل الصفحة لتحديث القائمة
            st.rerun()

def future_tasks_page():
    st.title("⏳ مهام آجلة")
    st.markdown("مكان لإدارة المهام التي تريد تنفيذها في تاريخ محدد")
    
    # تحميل المهام المسبقة إذا وجدت
    tasks_file = "future_tasks.json"
    tasks = []  # تهيئة القائمة فارغة
    
    # معالجة حالة الملف غير موجود أو فارغ
    try:
        if os.path.exists(tasks_file):
            with open(tasks_file, "r", encoding="utf-8") as f:
                file_content = f.read()
                if file_content.strip():  # التأكد من أن الملف ليس فارغاً
                    tasks = json.loads(file_content)
    except (json.JSONDecodeError, FileNotFoundError):
        st.warning("⚠️ حدث خطأ في قراءة ملف المهام، سيتم إنشاء ملف جديد")
        tasks = []
    
    # قسم إضافة مهمة جديدة
    st.subheader("إضافة مهمة جديدة")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        new_task = st.text_input("وصف المهمة:")
    
    with col2:
        task_date = st.date_input(
            "تاريخ التنفيذ:",
            min_value=date.today(),
            value=date.today() + timedelta(days=1)
        )
    
    if st.button("➕ إضافة المهمة"):
        if new_task:
            tasks.append({
                "task": new_task,
                "date": task_date.strftime("%Y-%m-%d"),
                "completed": False
            })
            try:
                with open(tasks_file, "w", encoding="utf-8") as f:
                    json.dump(tasks, f, ensure_ascii=False, indent=4)
                st.success("تم إضافة المهمة بنجاح!")
                st.rerun()  # إعادة تحميل الصفحة لتحديث القائمة
            except Exception as e:
                st.error(f"حدث خطأ أثناء الحفظ: {e}")
        else:
            st.warning("الرجاء إدخال وصف للمهمة")
    
    st.markdown("---")
    
    # قسم عرض المهام
    st.subheader("قائمة المهام الآجلة")
    
    # فلترة المهام حسب التاريخ
    filter_option = st.selectbox("تصفية المهام:", [
        "جميع المهام",
        "المهام القادمة",
        "المهام المنتهية",
        "المهام المتأخرة"
    ])
    
    today = date.today()
    filtered_tasks = []
    
    for task in tasks:
        task_date = datetime.strptime(task["date"], "%Y-%m-%d").date()
        if filter_option == "جميع المهام":
            filtered_tasks.append(task)
        elif filter_option == "المهام القادمة" and not task["completed"] and task_date >= today:
            filtered_tasks.append(task)
        elif filter_option == "المهام المنتهية" and task["completed"]:
            filtered_tasks.append(task)
        elif filter_option == "المهام المتأخرة" and not task["completed"] and task_date < today:
            filtered_tasks.append(task)
    
    # ترتيب المهام حسب التاريخ (الأقدم أولاً)
    filtered_tasks.sort(key=lambda x: x["date"])
    
    if not filtered_tasks:
        st.info("لا توجد مهام لعرضها حسب الفلتر المحدد")
    else:
        for i, task in enumerate(filtered_tasks):
            task_date = datetime.strptime(task["date"], "%Y-%m-%d").date()
            is_past_due = not task["completed"] and task_date < today
            
            col1, col2, col3, col4 = st.columns([1, 3, 1, 1])  # إضافة عمود جديد للحذف
            
            with col1:
                status = "✅" if task["completed"] else ("⚠️" if is_past_due else "⏳")
                st.markdown(f"**{status}**")
            
            with col2:
                date_color = "red" if is_past_due else ("green" if task["completed"] else "blue")
                st.markdown(f"""
                **{task['task']}**  
                <span style='color: {date_color}'>📅 {task['date']}</span>
                """, unsafe_allow_html=True)
            
            with col3:
                if not task["completed"]:
                    if st.button("✔️ إنجاز", key=f"complete_{i}"):
                        tasks[tasks.index(task)]["completed"] = True
                        with open(tasks_file, "w", encoding="utf-8") as f:
                            json.dump(tasks, f, ensure_ascii=False, indent=4)
                        st.rerun()
                else:
                    if st.button("↩️ إلغاء", key=f"undo_{i}"):
                        tasks[tasks.index(task)]["completed"] = False
                        with open(tasks_file, "w", encoding="utf-8") as f:
                            json.dump(tasks, f, ensure_ascii=False, indent=4)
                        st.rerun()
            
            with col4:
                if st.button("🗑️ حذف", key=f"delete_{i}"):
                    tasks.remove(task)
                    with open(tasks_file, "w", encoding="utf-8") as f:
                        json.dump(tasks, f, ensure_ascii=False, indent=4)
                    st.success("تم حذف المهمة بنجاح!")
                    time.sleep(0.5)  # تأخير بسيط لعرض الرسالة
                    st.rerun()
            
            st.markdown("---")
# صفحة فارغة

def empty_page():
    st.write("")

# تشغيل الصفحة المختارة
if page == "الصفحة الرئيسية":
    home_page()
elif page == "الجدول اليومي":
    daily_schedule_page()
elif page == "فيديوهات التمارين":
    workout_videos_page()
elif page == "أذكار":
    azkark_page()
elif page == "جدول القرآن":
    quran_schedule_page()
elif page == "افكاري":
    ideas_page()
elif page == "مهام آجلة":
    future_tasks_page() 