import streamlit as st
import datetime
from pathlib import Path
from profile_engine import compute_profile, get_compatibility

st.set_page_config(
    page_title="Psychotyp",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Состояние ──────────────────────────────────────────────────────────────
for k,v in {
    "step": "landing",
    "lang": "EN",
    "p1": None, "p2": None,
    "mode": "personal",
    "quiz": None,
    "quiz_answers": {},
    "cog_done": False,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

L = st.session_state.lang

# ── Переводы ───────────────────────────────────────────────────────────────
T = {
    "title": {"EN": "Psychotyp", "RU": "Психотип"},
    "subtitle": {
        "EN": "Your neural architecture — based on prenatal solar dynamics",
        "RU": "Ваша нейронная архитектура — на основе пренатальной солнечной динамики",
    },
    "landing_h1": {
        "EN": "What is your brain actually built for?",
        "RU": "Для чего реально построен ваш мозг?",
    },
    "landing_p1": {
        "EN": """Standard personality tests measure *behaviour*.  
Psychotyp measures the **architecture** behind it — the neural structure formed 
during your critical developmental windows, shaped by electromagnetic solar dynamics.  

This is not astrology. The mechanism is biophysical. The data is measured.  
The results are falsifiable.""",
        "RU": """Стандартные тесты личности измеряют *поведение*.  
Psychotyp измеряет **архитектуру** за ним — нейронную структуру, сформированную  
в критические окна развития под влиянием электромагнитной солнечной динамики.  

Это не астрология. Механизм биофизический. Данные измерены.  
Результаты фальсифицируемы.""",
    },
    "how_title": {
        "EN": "How it works",
        "RU": "Как это работает",
    },
    "how_steps": {
        "EN": [
            "**Step 1 — Neural Architecture Profile**  \nYour date of birth → prenatal solar dynamics → RS1-RS4 axes → 8 functional indices",
            "**Step 2 — Cognitive Test** *(optional)*  \nReaction time, working memory, interference control → measured performance vs. predicted baseline",
            "**Step 3 — Targeted Questionnaire** *(optional)*  \nBurnout / Compatibility / AI collaboration → behavioral layer on top of architecture",
            "**Step 4 — Integrated Report**  \nGAP analysis: where architecture and behavior diverge — and what to do about it",
        ],
        "RU": [
            "**Шаг 1 — Профиль нейронной архитектуры**  \nДата рождения → солнечная динамика → оси RS1-RS4 → 8 функциональных индексов",
            "**Шаг 2 — Когнитивный тест** *(опционально)*  \nВремя реакции, рабочая память, контроль интерференции → измеренные показатели vs. предсказанный базовый уровень",
            "**Шаг 3 — Целевой опросник** *(опционально)*  \nВыгорание / Совместимость / Работа с ИИ → поведенческий слой поверх архитектуры",
            "**Шаг 4 — Интегрированный отчёт**  \nGAP-анализ: где архитектура и поведение расходятся — и что с этим делать",
        ],
    },
    "start_btn": {"EN": "Start — Get My Profile", "RU": "Начать — Получить профиль"},
    "name_label": {"EN": "Name (optional)", "RU": "Имя (опционально)"},
    "sex_label": {"EN": "Sex", "RU": "Пол"},
    "sex_opts": {"EN": ["Male", "Female"], "RU": ["Мужской", "Женский"]},
    "dob_label": {"EN": "Date of Birth", "RU": "Дата рождения"},
    "compute_btn": {"EN": "Compute My Profile →", "RU": "Вычислить профиль →"},
    "computing": {"EN": "Analyzing solar dynamics...", "RU": "Анализ солнечной динамики..."},
    "mode_label": {"EN": "Mode", "RU": "Режим"},
    "mode_opts": {"EN": ["Personal Profile", "Compatibility"], "RU": ["Личный профиль", "Совместимость"]},
    "p1_label": {"EN": "Partner 1", "RU": "Партнёр 1"},
    "p2_label": {"EN": "Partner 2", "RU": "Партнёр 2"},
    "compat_btn": {"EN": "Analyze Compatibility →", "RU": "Анализировать совместимость →"},
    "key_insights": {"EN": "Key Insights", "RU": "Ключевые инсайты"},
    "recommendations": {"EN": "Recommendations", "RU": "Рекомендации"},
    "next_cog": {"EN": "→ Take Cognitive Test", "RU": "→ Пройти когнитивный тест"},
    "next_quiz": {"EN": "→ Choose Questionnaire", "RU": "→ Выбрать опросник"},
    "back": {"EN": "← Back", "RU": "← Назад"},
    "restart": {"EN": "Start Over", "RU": "Начать заново"},
    "cog_title": {"EN": "Cognitive Assessment", "RU": "Когнитивная оценка"},
    "cog_desc": {
        "EN": "5 short tests (15 min). Measures your actual reaction time, working memory, and cognitive control — compared against your architectural prediction.",
        "RU": "5 коротких тестов (15 минут). Измеряет ваше реальное время реакции, рабочую память и когнитивный контроль — в сравнении с архитектурным предсказанием.",
    },
    "cog_done_btn": {"EN": "Tests Complete → View Results", "RU": "Тесты пройдены → Смотреть результаты"},
    "quiz_title": {"EN": "Choose Your Questionnaire", "RU": "Выберите опросник"},
    "quiz_opts": {
        "EN": {
            "compatibility": "💞 Compatibility — understand relationship dynamics",
            "burnout": "🔥 Burnout Audit — measure your current resource load",
            "ai": "🤖 AI Collaboration — how your architecture interacts with AI",
        },
        "RU": {
            "compatibility": "💞 Совместимость — понять динамику отношений",
            "burnout": "🔥 Аудит выгорания — измерить текущую ресурсную нагрузку",
            "ai": "🤖 Работа с ИИ — как ваша архитектура взаимодействует с ИИ",
        },
    },
    "submit_quiz": {"EN": "Submit Answers →", "RU": "Отправить ответы →"},
    "scale_label": {"EN": "1 = Never / Strongly disagree  |  5 = Always / Strongly agree",
                    "RU": "1 = Никогда / Совершенно не согласен  |  5 = Всегда / Полностью согласен"},
    "compat_score": {"EN": "Compatibility Index", "RU": "Индекс совместимости"},
    "pair_dynamics": {"EN": "Pair Dynamics", "RU": "Динамика пары"},
    "validation_note": {
        "EN": "Validated on LEMON dataset (n=199). Significant associations with anxiety (ρ=0.20), impulsivity (ρ=0.26), stress (ρ=0.23).",
        "RU": "Валидировано на датасете LEMON (n=199). Значимые связи с тревогой (ρ=0.20), импульсивностью (ρ=0.26), стрессом (ρ=0.23).",
    },
}

def t(key):
    return T.get(key, {}).get(L, T.get(key, {}).get("EN", key))

# ── Опросники ──────────────────────────────────────────────────────────────
QUESTIONS = {
    "compatibility": {
        "EN": [
            "When we disagree, I feel heard and understood.",
            "I find it easy to express what I need from my partner.",
            "After a difficult conversation, I feel relief rather than tension.",
            "I can raise an uncomfortable topic without fearing a negative reaction.",
            "We talk about important things before they become problems.",
            "Our arguments end with a resolution, not just exhaustion.",
            "After conflict, we return to closeness fairly quickly.",
            "I feel safe being wrong or admitting a mistake with my partner.",
            "We have compatible needs for alone time and togetherness.",
            "We want the same things from life in the next 5 years.",
            "We support each other's individual goals, not just shared ones.",
            "Being with my partner restores my energy rather than draining it.",
        ],
        "RU": [
            "Когда мы не соглашаемся, я чувствую что меня слышат и понимают.",
            "Мне легко сказать партнёру чего я хочу или в чём нуждаюсь.",
            "После трудного разговора я чувствую облегчение, а не напряжение.",
            "Я могу поднять неудобную тему не опасаясь негативной реакции.",
            "Мы говорим о важных вещах до того, как они становятся проблемами.",
            "Наши ссоры заканчиваются решением, а не просто истощением.",
            "После конфликта мы довольно быстро возвращаемся к близости.",
            "Я чувствую безопасность признавая ошибку перед партнёром.",
            "У нас совместимые потребности в одиночестве и близости.",
            "Мы хотим одного и того же от жизни в следующие 5 лет.",
            "Мы поддерживаем индивидуальные цели друг друга.",
            "Пребывание с партнёром восстанавливает мою энергию.",
        ],
    },
    "burnout": {
        "EN": [
            "By end of day I feel completely drained, even if nothing major happened.",
            "I wake up tired, before the day has even started.",
            "Small tasks require effort that feels disproportionate.",
            "My body carries tension that doesn't go away even after rest.",
            "I feel emotionally distant from people I used to care about at work.",
            "I find myself going through the motions rather than being genuinely engaged.",
            "I have become more cynical or irritable about things that used to matter.",
            "My work no longer has the meaning it once did.",
            "I still produce good work but it costs me much more than it used to.",
            "I struggle to concentrate on one thing for more than 20-30 minutes.",
            "My sleep doesn't feel restorative — I still wake up tired.",
            "Activities that used to recharge me no longer work the same way.",
        ],
        "RU": [
            "К концу дня я чувствую себя полностью опустошённым.",
            "Я просыпаюсь усталым ещё до начала дня.",
            "Небольшие задачи требуют несоразмерных усилий.",
            "Моё тело несёт напряжение которое не уходит даже после отдыха.",
            "Я чувствую эмоциональную дистанцию от людей на работе.",
            "Я замечаю что просто делаю движения, а не реально включён.",
            "Я стал более циничным по отношению к вещам которые раньше имели значение.",
            "Моя работа больше не имеет того смысла что был раньше.",
            "Я ещё могу делать хорошую работу, но это стоит значительно больше.",
            "Мне трудно сосредоточиться дольше 20-30 минут.",
            "Мой сон не восстанавливает — я всё равно просыпаюсь усталым.",
            "Занятия которые раньше восстанавливали меня больше не работают.",
        ],
    },
    "ai": {
        "EN": [
            "I tend to accept AI outputs without extensively checking them.",
            "When AI gives a confident answer, I feel uncomfortable doubting it.",
            "I can tell when an AI response is plausible but wrong.",
            "I actively look for errors or gaps in what AI produces.",
            "Using AI leaves me feeling mentally clearer and more productive.",
            "I sometimes feel more confused after using AI than before.",
            "I notice when I am delegating thinking to AI that I should do myself.",
            "My decisions improved after I started using AI regularly.",
            "I use AI to challenge my thinking, not just confirm it.",
            "I trust my own judgment more than AI when they conflict.",
            "I am aware of how my emotional state affects my AI prompts.",
            "I can clearly explain why I accepted or rejected an AI suggestion.",
        ],
        "RU": [
            "Я склонен принимать результаты ИИ без тщательной проверки.",
            "Когда ИИ даёт уверенный ответ, мне некомфортно сомневаться.",
            "Я могу определить когда ответ ИИ правдоподобен, но неверен.",
            "Я активно ищу ошибки или пробелы в том что производит ИИ.",
            "Использование ИИ оставляет меня ментально более ясным.",
            "Иногда после ИИ я чувствую себя более запутанным чем до.",
            "Я замечаю когда делегирую ИИ мышление которое должен делать сам.",
            "Мои решения улучшились после того как я начал регулярно использовать ИИ.",
            "Я использую ИИ чтобы оспорить своё мышление, а не просто подтвердить.",
            "Я доверяю своему суждению больше чем ИИ когда они конфликтуют.",
            "Я осознаю как моё эмоциональное состояние влияет на запросы к ИИ.",
            "Я могу объяснить почему принял или отклонил предложение ИИ.",
        ],
    },
}

def score_quiz(answers, quiz_type):
    vals = list(answers.values())
    if not vals:
        return 0, "—"
    avg = sum(vals) / len(vals)
    pct = int((avg - 1) / 4 * 100)
    if quiz_type == "burnout":
        if pct < 35:
            label = {"EN": "Low risk", "RU": "Низкий риск"}[L]
        elif pct < 60:
            label = {"EN": "Moderate — monitor", "RU": "Умеренный — наблюдайте"}[L]
        else:
            label = {"EN": "High — action needed", "RU": "Высокий — нужны действия"}[L]
    elif quiz_type == "compatibility":
        if pct > 65:
            label = {"EN": "Strong connection", "RU": "Сильная связь"}[L]
        elif pct > 40:
            label = {"EN": "Moderate — growth areas visible", "RU": "Умеренная — видны зоны роста"}[L]
        else:
            label = {"EN": "Challenging — conscious work needed", "RU": "Сложная — нужна осознанная работа"}[L]
    else:
        if pct > 65:
            label = {"EN": "Optimal AI collaborator", "RU": "Оптимальное взаимодействие с ИИ"}[L]
        elif pct > 40:
            label = {"EN": "Moderate — calibration needed", "RU": "Умеренное — нужна калибровка"}[L]
        else:
            label = {"EN": "Risk of over-delegation", "RU": "Риск избыточного делегирования"}[L]
    return pct, label

# ═══════════════════════════════════════════════════════════════════════════
# ЭКРАН 0: Выбор языка (всегда вверху)
# ═══════════════════════════════════════════════════════════════════════════
col_lang = st.columns([4,1])[1]
new_lang = col_lang.selectbox("🌐", ["EN","RU"],
    index=0 if st.session_state.lang=="EN" else 1,
    label_visibility="collapsed")
if new_lang != st.session_state.lang:
    st.session_state.lang = new_lang
    L = new_lang
    st.rerun()

# ═══════════════════════════════════════════════════════════════════════════
# ЭКРАН 1: Лендинг
# ═══════════════════════════════════════════════════════════════════════════
if st.session_state.step == "landing":
    st.title(t("title") + " 🧠")
    st.caption(t("subtitle"))
    st.divider()
    st.header(t("landing_h1"))
    st.markdown(t("landing_p1"))
    st.divider()
    st.subheader(t("how_title"))
    for step_text in t("how_steps"):
        st.markdown(step_text)
    st.divider()
    st.caption(t("validation_note"))
    st.divider()
    mode = st.radio(t("mode_label"), t("mode_opts"), horizontal=True)
    st.session_state.mode = "compat" if mode == t("mode_opts")[-1] else "personal"
    if st.button(t("start_btn"), use_container_width=True, type="primary"):
        st.session_state.step = "input"
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════
# ЭКРАН 2: Ввод данных
# ═══════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "input":
    st.title(t("title") + " 🧠")
    if st.session_state.mode == "personal":
        col1, col2 = st.columns(2)
        name = col1.text_input(t("name_label"), placeholder="...")
        sex  = col2.selectbox(t("sex_label"), t("sex_opts"))
        dob  = st.date_input(t("dob_label"),
               value=datetime.date(1985,6,15),
               min_value=datetime.date(1920,1,1),
               max_value=datetime.date.today()-datetime.timedelta(days=365*16))
        if st.button(t("compute_btn"), use_container_width=True, type="primary"):
            with st.spinner(t("computing")):
                st.session_state.p1 = compute_profile(dob, sex, name or "—", L)
            st.session_state.step = "result"
            st.rerun()
    else:
        st.subheader(t("p1_label"))
        c1, c2 = st.columns(2)
        n1 = c1.text_input(t("name_label"), key="n1", placeholder="...")
        s1 = c1.selectbox(t("sex_label"), t("sex_opts"), key="s1")
        d1 = c2.date_input(t("dob_label"), value=datetime.date(1985,3,10),
             min_value=datetime.date(1920,1,1),
             max_value=datetime.date.today(), key="d1")
        st.subheader(t("p2_label"))
        c3, c4 = st.columns(2)
        n2 = c3.text_input(t("name_label"), key="n2", placeholder="...")
        s2 = c3.selectbox(t("sex_label"), t("sex_opts"), key="s2")
        d2 = c4.date_input(t("dob_label"), value=datetime.date(1988,9,22),
             min_value=datetime.date(1920,1,1),
             max_value=datetime.date.today(), key="d2")
        if st.button(t("compat_btn"), use_container_width=True, type="primary"):
            with st.spinner(t("computing")):
                st.session_state.p1 = compute_profile(d1, s1, n1 or "P1", L)
                st.session_state.p2 = compute_profile(d2, s2, n2 or "P2", L)
            st.session_state.step = "compat"
            st.rerun()
    if st.button(t("back")):
        st.session_state.step = "landing"
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════
# ЭКРАН 3: Результат — личный профиль
# ═══════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "result":
    p = st.session_state.p1
    st.title(p.get("name","") + " — " + p.get("type_name",""))
    st.caption(p.get("tagline",""))
    st.divider()

    # RS-оси
    col1,col2,col3,col4 = st.columns(4)
    rs4 = p.get("rs4",50)
    col1.metric("RS4", f"{rs4:.0f}")
    col2.metric("Tension", f"{p.get('tension',40):.0f}")
    col3.metric("RS2", f"{p.get('rs2',50):.0f}")
    col4.metric("Adaptive", f"{p.get('adaptive',50):.0f}")

    st.progress(min(int(p.get("rs1",50)),100)/100,
                text=f"RS1 Rhythm: {p.get('rs1',50):.0f}")
    st.progress(min(int(p.get("rs2",50)),100)/100,
                text=f"RS2 Sync: {p.get('rs2',50):.0f}")
    st.progress(min(int(p.get("rs3",50)),100)/100,
                text=f"RS3 Topology: {p.get('rs3',50):.0f}")
    st.progress(min(int(rs4),100)/100,
                text=f"RS4 Integration: {rs4:.0f}")
    st.divider()

    # Интерпретация через interpret_engine
    try:
        from interpret_engine import interpret
        raw = p.get("raw", {})
        if raw:
            interp = interpret(raw, L)
            st.subheader({"EN":"Functional Profile","RU":"Функциональный профиль"}[L])
            for idx_name, idx_data in interp["indices"].items():
                level = idx_data["level"]
                icon = "🔴" if level=="high" and idx_name in ("overload","emo_cost","bottleneck","rigidity","transition_cost","autonomic") else \
                       "🟢" if level=="low" and idx_name in ("overload","emo_cost","bottleneck") else "🟡"
                with st.expander(f"{icon} {idx_data['title']}"):
                    st.write(idx_data["description"])
            st.divider()
            if interp.get("gap_text"):
                st.info(interp["gap_text"])
        else:
            raise Exception("no raw")
    except Exception:
        st.subheader(t("key_insights"))
        for ins in p.get("insights",[]):
            st.info(ins)

    st.subheader(t("recommendations"))
    for rec in p.get("recommendations",[]):
        st.success("✓ " + rec)

    st.divider()
    c1, c2, c3 = st.columns(3)
    if c1.button(t("next_cog"), use_container_width=True):
        st.session_state.step = "cognitive"
        st.rerun()
    if c2.button(t("next_quiz"), use_container_width=True):
        st.session_state.step = "quiz_select"
        st.rerun()
    if c3.button(t("restart")):
        for k in ["p1","p2","quiz","quiz_answers","cog_done"]:
            st.session_state[k] = None if k in ["p1","p2","quiz"] else {} if k=="quiz_answers" else False
        st.session_state.step = "landing"
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════
# ЭКРАН 4: Когнитивный тест
# ═══════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "cognitive":
    st.title(t("cog_title") + " 🧪")
    st.write(t("cog_desc"))
    st.divider()
    html_path = Path(__file__).parent / "cognitive_test.html"
    if html_path.exists():
        with open(html_path,"r",encoding="utf-8") as f:
            st.components.v1.html(f.read(), height=750, scrolling=True)
    else:
        st.warning("cognitive_test.html not found in app folder.")
        st.info("Place the file 'stage2_cognitive_v6_speed_accuracy_public_v2_name_dob.html' "
                "renamed as 'cognitive_test.html' in ~/psychotyp_site/")
    st.divider()
    c1, c2 = st.columns(2)
    if c1.button(t("cog_done_btn"), type="primary"):
        st.session_state.cog_done = True
        st.session_state.step = "quiz_select"
        st.rerun()
    if c2.button(t("back")):
        st.session_state.step = "result"
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════
# ЭКРАН 5: Выбор опросника
# ═══════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "quiz_select":
    st.title(t("quiz_title") + " 📋")
    st.divider()
    quiz_opts = t("quiz_opts")
    for qkey, qlabel in quiz_opts.items():
        if st.button(qlabel, use_container_width=True):
            st.session_state.quiz = qkey
            st.session_state.quiz_answers = {}
            st.session_state.step = "quiz"
            st.rerun()
    st.divider()
    if st.button(t("back")):
        st.session_state.step = "result" if not st.session_state.cog_done else "cognitive"
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════
# ЭКРАН 6: Опросник
# ═══════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "quiz":
    quiz_type = st.session_state.quiz
    quiz_name = t("quiz_opts").get(quiz_type, quiz_type)
    st.title(quiz_name)
    st.caption(t("scale_label"))
    st.divider()

    questions = QUESTIONS.get(quiz_type, {}).get(L, QUESTIONS.get(quiz_type,{}).get("EN",[]))
    answers = {}
    for i, q in enumerate(questions):
        answers[i] = st.slider(
            f"{i+1}. {q}",
            min_value=1, max_value=5, value=3,
            key=f"q_{quiz_type}_{i}"
        )

    st.divider()
    c1, c2 = st.columns(2)
    if c1.button(t("submit_quiz"), type="primary", use_container_width=True):
        st.session_state.quiz_answers = answers
        st.session_state.step = "quiz_result"
        st.rerun()
    if c2.button(t("back")):
        st.session_state.step = "quiz_select"
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════
# ЭКРАН 7: Результат опросника + финальный отчёт
# ═══════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "quiz_result":
    p = st.session_state.p1
    quiz_type = st.session_state.quiz
    answers = st.session_state.quiz_answers
    score_pct, score_label = score_quiz(answers, quiz_type)

    quiz_name = t("quiz_opts").get(quiz_type, quiz_type)
    st.title({"EN":"Your Results","RU":"Ваши результаты"}[L] + " 📊")
    st.subheader(quiz_name)
    st.divider()

    # Профиль архитектуры сверху
    st.caption(p.get("type_name","") + " | " + p.get("tagline",""))
    c1,c2,c3 = st.columns(3)
    c1.metric("RS4", f"{p.get('rs4',50):.0f}")
    c2.metric("Tension", f"{p.get('tension',40):.0f}")
    c3.metric("Adaptive", f"{p.get('adaptive',50):.0f}")
    st.divider()

    # Результат опросника
    st.metric({"EN":"Questionnaire Score","RU":"Результат опросника"}[L],
              f"{score_pct}%", score_label)
    st.progress(score_pct/100)
    st.divider()

    # GAP: архитектура vs поведение
    st.subheader({"EN":"Architecture × Behavior GAP","RU":"GAP: Архитектура × Поведение"}[L])
    try:
        from interpret_engine import interpret
        raw = p.get("raw",{})
        if raw:
            interp = interpret(raw, L)
            overload_level = interp["index_levels"].get("overload","mid")
            emo_level = interp["index_levels"].get("emo_cost","mid")

            if quiz_type == "burnout":
                if score_pct > 60 and overload_level == "high":
                    st.error({"EN":"⚠️ High architectural load + high behavioral burnout. Immediate recovery protocol recommended.",
                              "RU":"⚠️ Высокая архитектурная нагрузка + высокое поведенческое выгорание. Рекомендован немедленный протокол восстановления."}[L])
                elif score_pct > 60 and overload_level == "low":
                    st.warning({"EN":"Burnout symptoms above architectural baseline. Situational overload — not structural.",
                                "RU":"Симптомы выгорания выше архитектурного базового уровня. Ситуационная перегрузка — не структурная."}[L])
                elif score_pct < 40 and overload_level == "high":
                    st.info({"EN":"Architecture carries high load but behavior is compensated. Hidden tension — monitor.",
                             "RU":"Архитектура несёт высокую нагрузку, но поведение компенсировано. Скрытое напряжение — наблюдайте."}[L])
                else:
                    st.success({"EN":"Architecture and burnout levels are aligned. System is functioning within expected range.",
                                "RU":"Архитектура и уровень выгорания согласованы. Система функционирует в ожидаемом диапазоне."}[L])

            elif quiz_type == "compatibility":
                if score_pct > 65:
                    st.success({"EN":"Strong behavioral connection. Your architecture supports this.",
                                "RU":"Сильная поведенческая связь. Ваша архитектура это поддерживает."}[L])
                else:
                    st.info({"EN":"Growth areas visible. Your architectural profile suggests specific strategies.",
                             "RU":"Видны зоны роста. Ваш архитектурный профиль предполагает конкретные стратегии."}[L])

            elif quiz_type == "ai":
                if score_pct > 65 and emo_level == "high":
                    st.warning({"EN":"Good AI calibration but high emotional cost. Stress may reduce critical evaluation of AI outputs.",
                                "RU":"Хорошая калибровка ИИ, но высокая эмоциональная стоимость. Стресс может снизить критическую оценку вывода ИИ."}[L])
                elif score_pct < 40:
                    st.error({"EN":"Risk of over-delegation. Your architecture may amplify this under load.",
                              "RU":"Риск избыточного делегирования. Ваша архитектура может усилить это под нагрузкой."}[L])
                else:
                    st.success({"EN":"Balanced AI collaboration profile.",
                                "RU":"Сбалансированный профиль взаимодействия с ИИ."}[L])
    except Exception:
        pass

    st.divider()
    c1, c2 = st.columns(2)
    if c1.button({"EN":"← Another Questionnaire","RU":"← Другой опросник"}[L]):
        st.session_state.step = "quiz_select"
        st.rerun()
    if c2.button(t("restart")):
        for k in ["p1","p2","quiz","quiz_answers","cog_done"]:
            st.session_state[k] = None if k in ["p1","p2","quiz"] else {} if k=="quiz_answers" else False
        st.session_state.step = "landing"
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════
# ЭКРАН 8: Совместимость пары
# ═══════════════════════════════════════════════════════════════════════════
elif st.session_state.step == "compat":
    p1 = st.session_state.p1
    p2 = st.session_state.p2
    compat = get_compatibility(p1, p2)
    score = compat["score"]

    st.title(f"{p1.get('name','P1')} & {p2.get('name','P2')}")
    st.divider()
    st.metric(t("compat_score"), f"{score}%", compat.get("summary",""))
    st.progress(score/100)
    st.divider()

    c1, c2 = st.columns(2)
    with c1:
        st.subheader(p1.get("name","P1"))
        st.caption(p1.get("type_name",""))
        st.metric("RS4", f"{p1.get('rs4',50):.0f}")
        st.metric("Tension", f"{p1.get('tension',40):.0f}")
        for ins in p1.get("insights",[])[:2]:
            st.info(ins)
    with c2:
        st.subheader(p2.get("name","P2"))
        st.caption(p2.get("type_name",""))
        st.metric("RS4", f"{p2.get('rs4',50):.0f}")
        st.metric("Tension", f"{p2.get('tension',40):.0f}")
        for ins in p2.get("insights",[])[:2]:
            st.info(ins)

    st.divider()
    st.subheader(t("pair_dynamics"))
    for d in compat.get("dynamics",[]):
        st.info(d)

    st.divider()
    if st.button(t("restart")):
        for k in ["p1","p2"]:
            st.session_state[k] = None
        st.session_state.step = "landing"
        st.rerun()
