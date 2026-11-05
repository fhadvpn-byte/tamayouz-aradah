"""منصة تميّز — تقارير جائزة معالي مدير الأمن العام، قسم مرور محافظة العارضة."""

from __future__ import annotations

import base64
import html
import io
import json
import shutil
import uuid
from pathlib import Path

import arabic_reshaper
import streamlit as st
from bidi.algorithm import get_display
from fpdf import FPDF
from PIL import Image

ROOT = Path(__file__).resolve().parent
FONT_REG = ROOT / "fonts" / "NotoNaskhArabic-Regular.ttf"
FONT_BOLD = ROOT / "fonts" / "NotoNaskhArabic-Bold.ttf"
FONT_LATIN = ROOT / "fonts" / "NotoSans-Regular.ttf"
FONT_LATIN_BOLD = ROOT / "fonts" / "NotoSans-Bold.ttf"

LOGO_FILE = ROOT / "traffic_logo.png"
_FALLBACK_LOGO = "data:image/svg+xml;utf8," + (
    "%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 160 160'%3E"
    "%3Ccircle cx='80' cy='80' r='74' fill='%230b4f26' stroke='%23c5a059' stroke-width='6'/%3E"
    "%3Ccircle cx='80' cy='80' r='64' fill='none' stroke='%23c5a059' stroke-width='2' stroke-dasharray='4,4'/%3E"
    "%3Ctext x='80' y='88' font-family='Tahoma,sans-serif' font-size='18' font-weight='bold' fill='%23ffffff' text-anchor='middle'%3Eالمرور%3C/text%3E"
    "%3C/svg%3E"
)


def load_permanent_traffic_logo() -> str:
    """يحمّل شعار المرور من مجلد المشروع، وينسخه من hasm-ai إن غاب محلياً."""
    search_paths = [
        LOGO_FILE,
        ROOT / "traffic_logo.png.png",
        ROOT / "logo.png",
        ROOT.parent / "hasm-ai" / "traffic_logo.png",
        ROOT.parent / "hasm-ai" / "traffic_logo.png.png",
        Path(r"C:\Users\Admin\Desktop\مشاريع\hasm-ai\traffic_logo.png"),
        Path(r"C:\Users\Admin\Desktop\مشاريع\hasm-ai\traffic_logo.png.png"),
    ]
    for path in search_paths:
        if not path.is_file():
            continue
        source = path
        if path.resolve() != LOGO_FILE.resolve():
            try:
                shutil.copy(path, LOGO_FILE)
                source = LOGO_FILE
            except OSError:
                source = path
        encoded = base64.b64encode(source.read_bytes()).decode("ascii")
        return f"data:image/png;base64,{encoded}"
    return _FALLBACK_LOGO


PERMANENT_LOGO = load_permanent_traffic_logo()

APP_CSS = """
<style>
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stSidebar"],
[data-testid="stMain"], [data-testid="stMainBlockContainer"], .stMarkdown, label, p, h1, h2, h3 {
  font-family: "Cairo", "Tahoma", "Segoe UI", sans-serif;
}
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stSidebar"],
[data-testid="stMain"], [data-testid="stMainBlockContainer"], .stMarkdown, label {
  direction: rtl;
  text-align: right;
}
[data-testid="stHeader"] { background: transparent; }
[data-testid="stDecoration"] { display: none; }
[data-testid="stMainBlockContainer"] { padding-top: 1.4rem; max-width: 1180px; }
[data-testid="stSidebar"] {
  border-left: 1px solid rgba(197, 160, 89, 0.45);
  border-right: none;
}
.tm-brand { padding: 0.2rem 0.1rem 0.9rem; border-bottom: 1px solid rgba(197, 160, 89, 0.35); margin-bottom: 0.8rem; }
.tm-brand h2 { margin: 0; color: #f6e7b4; font-size: 1.65rem; }
.tm-brand p { margin: 0.3rem 0 0; color: #d7ecdf; font-size: 0.86rem; line-height: 1.65; }
[data-testid="stSidebar"] [data-testid="stRadio"] [role="radiogroup"] { gap: 0.28rem; }
[data-testid="stSidebar"] [data-testid="stRadio"] label {
  border: 1px solid transparent;
  border-radius: 12px;
  padding: 0.55rem 0.7rem;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {
  background: linear-gradient(270deg, rgba(31, 138, 76, 0.35), rgba(197, 160, 89, 0.12));
  border-color: rgba(197, 160, 89, 0.75);
}
input, textarea, [data-baseweb="select"] > div {
  direction: rtl;
  text-align: right;
}
[data-testid="stAlert"], [data-testid="stExpander"] { direction: rtl; text-align: right; }
.top-banner {
  background: linear-gradient(135deg, #062b1f 0%, #0b4f38 100%);
  border: 1px solid #d4af37;
  border-radius: 14px;
  padding: 16px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 15px;
  margin-bottom: 18px;
}
.top-banner img {
  width: 72px;
  height: 72px;
  object-fit: contain;
  background: #ffffff;
  border-radius: 50%;
  padding: 5px;
  border: 2px solid #d4af37;
  flex: 0 0 auto;
}
.top-banner h2 { color: #ffffff; margin: 4px 0; font-weight: 900; font-size: 1.35rem; }
.top-banner .kicker { color: #d4af37; font-weight: 700; font-size: 0.9rem; }
.top-banner .lede { color: #bfe3cc; font-size: 0.88rem; }
.st-key-tm_sections [data-baseweb="tab-list"] {
  gap: 4px;
  overflow-x: auto;
  flex-wrap: nowrap;
}
.st-key-tm_sections button[data-baseweb="tab"] {
  white-space: nowrap;
  flex: 0 0 auto;
}
</style>
"""

MOBILE_CSS = """
<style>
.st-key-tm_nav [role="radiogroup"] { width: 100%; gap: 0.35rem; }
.st-key-tm_nav label {
  width: 100%;
  max-width: 100%;
  margin: 0;
  box-sizing: border-box;
  white-space: normal !important;
  overflow: hidden;
}
.st-key-tm_nav [data-baseweb="radio"] {
  display: flex !important;
  width: 100%;
  align-items: flex-start;
  direction: rtl;
}
.st-key-tm_nav [data-baseweb="radio"] > div:first-child { display: none !important; }
.st-key-tm_nav label p,
[data-testid="stSidebar"] label p,
[data-testid="stSidebar"] button p {
  white-space: normal !important;
  overflow: visible !important;
  text-overflow: unset !important;
  overflow-wrap: break-word;
  word-wrap: break-word;
  line-height: 1.5;
  text-align: right;
  margin: 0;
}
[data-testid="stSidebar"] {
  overflow-x: hidden;
}
[data-testid="stSidebar"] button {
  white-space: normal !important;
  height: auto !important;
  min-height: 2.4rem;
  line-height: 1.45;
}
[data-testid="stSidebar"] [data-testid="stCheckbox"] label {
  align-items: flex-start;
  width: 100%;
}
[data-testid="stAppViewContainer"]:has([data-testid="stExpandSidebarButton"]) section[data-testid="stSidebar"] {
  transform: translateX(115%) !important;
  pointer-events: none !important;
  visibility: hidden !important;
}
@media (max-width: 768px) {
  [data-testid="stMainBlockContainer"], .main .block-container {
    padding: 4.5rem 0.85rem 2.4rem !important;
    max-width: 100% !important;
  }
  [data-testid="stHeading"] h1,
  [data-testid="stHeading"] h2,
  h1, h2, h3, p, label, .stMarkdown, [data-testid="stCaption"] {
    overflow-wrap: break-word;
    word-wrap: break-word;
    line-height: 1.65;
  }
  [data-testid="stHeading"] h1, h1 { font-size: 1.45rem !important; }
  [data-testid="stHeading"] h2, h2 { font-size: 1.2rem !important; }
  [data-testid="stMetricValue"] { font-size: 1.25rem !important; overflow-wrap: anywhere; }
  section[data-testid="stSidebar"] {
    width: min(88vw, 22rem) !important;
    min-width: 0 !important;
    max-width: min(88vw, 22rem) !important;
    z-index: 1000001;
  }
  [data-testid="stExpandSidebarButton"] {
    position: fixed !important;
    top: 0.6rem !important;
    left: 0.6rem !important;
    right: auto !important;
    z-index: 1000005 !important;
    border-radius: 12px !important;
    border: 1px solid #c5a059 !important;
    background: #0c2418 !important;
  }
  .tm-brand h2 { font-size: 1.3rem; }
  .tm-brand p { font-size: 0.82rem; }
}
</style>
"""


def _uid(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def _photo(caption: str = "") -> dict:
    return {"uid": _uid("pic"), "src": "", "caption": caption}


def default_report() -> dict:
    return {
        "logo": "",
        "title": "تقرير المنظومة الرقمية وورش العمل التثقيفية وتقييم الانضباط السلوكي بشأن جائزة معالي مدير الأمن العام",
        "subtitle": "نموذج التحول الرقمي والانضباط المؤسسي والميداني بقسم مرور محافظة العارضة",
        "hijri": "٢٤ / ٠٥ / ١٤٤٨ هـ",
        "greg": "٢٠٢٦/١١/٠٤ م",
        "ref": "ت م / ع / ١٤٤٨/٠١",
        "manager": "رئيس رقباء / سلمان بن علي دوشي",
        "author": "رئيس قسم الحوادث / فهد أحمد بن محمد مجرشي",
        "exec": (
            "انطلاقاً من توجيهات قيادة الأمن العام والإدارة العامة للمرور، وحرصاً من قسم مرور محافظة العارضة "
            "التابع لإدارة مرور منطقة جازان على تحقيق أعلى معايير جائزة معالي مدير الأمن العام للانضباط السلوكي "
            "تحت شعار (هدفنا أمن وتواصل)، يقدّم هذا التقرير توثيقاً عملياً لتفعيل منظومات (حسم، رقابة، بينة)، "
            "وعقد ورش العمل التثقيفية، وتقييم الأفراد المتميزين، والارتقاء بالأداء الميداني."
        ),
        "showGov": True,
        "showAxes": True,
        "showApps": True,
        "showStaff": True,
        "showWorkshops": True,
        "showField": True,
        "showKpi": True,
        "staffCount": "30 فرداً",
        "discRate": "100%",
        "sysCount": "3 أنظمة ذكية",
        "violations": "صفر (0)",
        "govText": (
            "يعمل قسم مرور محافظة العارضة بكادر متكامل قوامه (30) فرداً من الكفاءات الميدانية والإدارية، "
            "وفق حوكمة داخلية تشمل التوجيه اليومي قبل استلام المهام، والالتزام بالقيافة والمظهر العسكري، "
            "والانضباط في أوقات الاستلام والتسليم، ومتابعة الأداء لحظياً."
        ),
        "valText": (
            "تُرجمت قيمة المسؤولية (أداء الواجب بإتقان، والوفاء بالالتزامات، وتحمل النتائج) إلى إجراءات "
            "مؤتمتة تمنع الاجتهاد الشخصي، وتسرّع إنهاء معاملات المستفيدين، وتوثّق المهام بشفافية."
        ),
        "axes": [
            {
                "uid": "axis-1",
                "name": "الانضباط السلوكي والقيافة",
                "motto": "المظهر العسكري والالتزام اليومي",
                "indicator": "100% التزام بالقيافة والمواعيد",
                "enabled": True,
                "text": "يلتزم أفراد القسم بالقيافة العسكرية والمظهر اللائق، وينضبطون في الاستلام والتسليم، مع توجيه يومي مسبق قبل مباشرة المهام.",
                "photos": [],
            },
            {
                "uid": "axis-2",
                "name": "المسؤولية وأداء الواجب بإتقان",
                "motto": "الوفاء بالالتزام وتحمل النتيجة",
                "indicator": "إسناد المهمة لصاحبها وتوثيق إنجازها",
                "enabled": True,
                "text": "تُدار المهام بمسؤولية مباشرة: كل إجراء له مالك، ووقت إنجاز، وأثر موثّق، بما يجسّد أداء الواجب بإتقان لا باجتهاد فردي متفرق.",
                "photos": [],
            },
            {
                "uid": "axis-3",
                "name": "الحوكمة والانضباط الإداري",
                "motto": "تعليمات واضحة ومتابعة لحظية",
                "indicator": "حوكمة يومية لثلاثين فرداً",
                "enabled": True,
                "text": "تُدار القوة البشرية وفق تعليمات معلنة ومتابعة مستمرة، من التوجيه قبل المهمة حتى تسليمها، وبلا مخالفات مسلكية مسجّلة.",
                "photos": [],
            },
            {
                "uid": "axis-4",
                "name": "الأمانة والنزاهة",
                "motto": "توثيق يمنع الاجتهاد الخفي",
                "indicator": "صفر مخالفات مسلكية",
                "enabled": True,
                "text": "يُوثَّق العمل رقمياً حتى لا يُترك الإجراء لتقدير غير منضبط، وتُحفظ بيانات المستفيدين والمركبات بأمانة وسرية مهنية.",
                "photos": [],
            },
            {
                "uid": "axis-5",
                "name": "العدل والحياد",
                "motto": "إسناد نظامي لنسب المسؤولية",
                "indicator": "تقارير بينة وفق نظام المرور",
                "enabled": True,
                "text": "تُحلَّل الحوادث وتُسنَد نسب المسؤولية وفق مواد نظام المرور عبر منظومة بينة، بعيداً عن الانحياز أو التفاوت في التقدير.",
                "photos": [],
            },
            {
                "uid": "axis-6",
                "name": "الاحترام وحسن التعامل",
                "motto": "كرامة المستفيد وسرعة الإنجاز",
                "indicator": "إنهاء الإجراءات بلا تأخير",
                "enabled": True,
                "text": "يُقابل المراجع باحترام، وتُختصر إجراءاته عبر منظومة حسم، بما يحفظ كرامة التعامل ويعكس صورة رجل المرور المنضبط.",
                "photos": [],
            },
            {
                "uid": "axis-7",
                "name": "المبادرة والجاهزية الميدانية",
                "motto": "انتشار مبكر على الطرق الجبلية",
                "indicator": "مباشرة البلاغات بوقت قياسي",
                "enabled": True,
                "text": "يبادر القسم بالانتشار على الطرق الجبلية والأودية قبل تفاقم الخطر، ويباشر الحوادث ويقدّم المساندة العاجلة لسائقي المركبات.",
                "photos": [],
            },
            {
                "uid": "axis-8",
                "name": "الإتقان وسرعة الإنجاز",
                "motto": "حسم الإجرائي بدل التفاوت",
                "indicator": "حوكمة الإجراءات عبر حسم",
                "enabled": True,
                "text": "اختصر التحول الرقمي تفاوت سرعة الإنجاز: حسم يضبط الإجراء، ورقابة تعرض المؤشر، وبينة تُخرج التقرير النظامي مباشرة.",
                "photos": [],
            },
            {
                "uid": "axis-9",
                "name": "التواصل والشراكة المجتمعية",
                "motto": "هدفنا أمن وتواصل",
                "indicator": "ندوات ومبادرات توعوية موثّقة",
                "enabled": True,
                "text": "يمتد الانضباط إلى الشراكة مع الجهات التعليمية والحكومية عبر ندوات ومبادرات السلامة المرورية، تعزيزاً لشعار الجائزة: هدفنا أمن وتواصل.",
                "photos": [],
            },
            {
                "uid": "axis-10",
                "name": "القدوة وتحفيز المتميزين",
                "motto": "تقييم معلن ولوحة شرف",
                "indicator": "معايير 40% / 30% / 20% / 10%",
                "enabled": True,
                "text": "تُقاس القدوة بمعايير معلنة: الانضباط العسكري، وإتقان الواجب، والتفاعل مع الأنظمة، والمبادرة الإنسانية، ويُبرَز المتميزون للترشيح.",
                "photos": [],
            },
        ],
        "apps": [
            {
                "uid": "app-hasm",
                "name": "منظومة «حسم» (HASM)",
                "impact": "حوكمة الإجراءات وسرعة الإنجاز والانضباط",
                "desc": "تطبيق ذكي يعزز سرعة الحسم الإجرائي في المعاملات والوقائع المرورية، ويمنع التأخير، ويجسّد الوفاء بالالتزام وإتقان الواجب.",
                "screenshot": "",
                "qr": "",
            },
            {
                "uid": "app-raqabah",
                "name": "منظومة «رقابة» (RAQABAH)",
                "impact": "الرقابة الذاتية والميدانية ومتابعة الانضباط",
                "desc": "نظام للمتابعة الإدارية والميدانية وحركة المركبات المحجوزة ومؤشرات الأداء، يضمن الانضباط السلوكي والالتزام بالتعليمات.",
                "screenshot": "",
                "qr": "",
            },
            {
                "uid": "app-bayyinah",
                "name": "منظومة «بينة» (BAYYINAH)",
                "impact": "العدالة والحياد في تحليل الحوادث",
                "desc": "منظومة لتحليل وصف الحوادث وإسنادها إلى مواد نظام المرور لتحديد نسب المسؤولية وإصدار تقارير PDF رسمية بنزاهة وشفافية.",
                "screenshot": "",
                "qr": "",
            },
        ],
        "staffList": [
            {
                "uid": "staff-1",
                "rank": "رئيس رقباء",
                "name": "سلمان بن علي دوشي",
                "role": "مدير قسم مرور محافظة العارضة",
                "s1": 100,
                "s2": 100,
                "s3": 100,
                "reason": "القيادة القدوة، والإشراف على ورش التثقيف بالجائزة، ودعم التحول الرقمي والانضباط الكامل بالقسم.",
            },
            {
                "uid": "staff-2",
                "rank": "رئيس قسم الحوادث",
                "name": "فهد أحمد بن محمد مجرشي",
                "role": "رئيس قسم الحوادث ومبتكر الأنظمة الرقمية",
                "s1": 100,
                "s2": 100,
                "s3": 100,
                "reason": "ابتكار وتطوير منظومات (حسم، رقابة، بينة) لتعزيز النزاهة والانضباط الإجرائي والميداني.",
            },
            {
                "uid": "staff-3",
                "rank": "فرد متميز",
                "name": "نموذج مرشح الانضباط الميداني (قابل للتعديل)",
                "role": "مباشرة الحوادث والميدان",
                "s1": 99,
                "s2": 98,
                "s3": 99,
                "reason": "الانضباط في القيافة، وسرعة الاستجابة على الطرق الجبلية، والتطبيق الدقيق للأنظمة.",
            },
        ],
        "workshops": [
            {
                "uid": "ws-1",
                "title": "ورشة عمل تثقيفية بشأن جائزة معالي مدير الأمن العام للانضباط السلوكي",
                "location": "مقر قسم مرور محافظة العارضة",
                "speaker": "مدير القسم رئيس رقباء / سلمان بن علي دوشي ورئيس قسم الحوادث / فهد أحمد مجرشي",
                "datetime": "الأربعاء ٢٤ / ٠٥ / ١٤٤٨ هـ - الساعة ١٠:٠٠ صباحاً",
                "target": "منسوبو قسم مرور محافظة العارضة (30 فرداً)",
                "outcomes": "شرح معايير الجائزة، وترسيخ المسؤولية وأداء الواجب بإتقان، وربط الانضباط السلوكي بتطبيقات حسم ورقابة وبينة.",
                "photos": [],
            }
        ],
        "showField": True,
        "fieldText": (
            "نظراً لطبيعة محافظة العارضة وما تضمه من طرق جبلية وعقبات وأودية، يطبّق الأفراد أعلى درجات الجاهزية: "
            "انتشار مبكر، ومباشرة الحوادث بوقت قياسي، ومساندة عاجلة لسائقي المركبات، تجسيداً لشعار (هدفنا أمن وتواصل)."
        ),
        "seminars": [
            {
                "uid": "sem-1",
                "title": "المبادرات التوعوية والندوات الميدانية للسلامة المرورية",
                "date": "الربع الثاني ١٤٤٨ هـ",
                "impact": "رفع الوعي المروري وتعزيز الشراكة مع الجهات التعليمية والحكومية.",
                "desc": "برامج توعوية وميدانية للحد من المخالفات المؤثرة على السلامة، وإبراز صورة رجل المرور المنضبط.",
                "photos": [],
            }
        ],
        "comparisons": [
            {
                "criterion": "معالجة وتحليل الحوادث المرورية",
                "before": "إجراءات ورقية تقليدية تستغرق وقتاً أطول",
                "after": "تحليل فوري وإسناد نظامي وإصدار PDF عبر «بينة»",
            },
            {
                "criterion": "متابعة الانضباط والمهام والمركبات",
                "before": "متابعة يدوية غير مؤتمتة",
                "after": "لوحة مؤشرات ورقابة لحظية عبر «رقابة»",
            },
            {
                "criterion": "سرعة الحسم الإجرائي والالتزام",
                "before": "تفاوت في سرعة إنجاز الإجراءات",
                "after": "حوكمة كاملة وسرعة إنجاز عبر «حسم»",
            },
            {
                "criterion": "الوعي بمعايير الجائزة",
                "before": "معرفة عامة غير موثقة بمؤشرات",
                "after": "استيعاب موثّق وتقييم تحفيزي للأفراد",
            },
        ],
        "pledge": (
            "نحن منسوبو قسم مرور محافظة العارضة نعاهد الله ثم ولاة أمرنا وقيادتنا على الالتزام بالانضباط السلوكي والعسكري، "
            "وأداء الواجب بإتقان وأمانة، والوفاء بالتزامات خدمة الوطن والمواطن والمقيم، وتحمل المسؤولية في تطبيق الأنظمة بعدل ونزاهة."
        ),
        "recommendations": (
            "١. استمرار تطوير الأنظمة الرقمية (حسم، رقابة، بينة) وتعميم تجربتها نموذجاً عملياً للانضباط.\n"
            "٢. عقد تقييم شهري لمؤشرات الانضباط السلوكي وتكريم الأفراد المتميزين.\n"
            "٣. توثيق المبادرات الميدانية والتقنية ورفعها دورياً للمرجع."
        ),
    }


def normalize(data: object) -> dict:
    base = default_report()
    if not isinstance(data, dict):
        return base
    for key, value in data.items():
        if key in base and value is not None:
            base[key] = value
    fallback = default_report()
    for key in ("axes", "apps", "staffList", "workshops", "seminars", "comparisons"):
        if not isinstance(base.get(key), list):
            base[key] = fallback[key]
    return base


def ensure_report(report: dict) -> None:
    for index, axis in enumerate(report["axes"]):
        if not isinstance(axis, dict):
            continue
        axis.setdefault("uid", f"axis-{index + 1}")
        axis.setdefault("name", f"المحور {index + 1}")
        axis.setdefault("motto", "")
        axis.setdefault("text", "")
        axis.setdefault("indicator", "")
        axis.setdefault("enabled", True)
        axis.setdefault("photos", [])
        _ensure_photos(axis["photos"])
    for index, app in enumerate(report["apps"]):
        app.setdefault("uid", f"app-{index + 1}")
        app.setdefault("name", "")
        app.setdefault("impact", "")
        app.setdefault("desc", "")
        app.setdefault("screenshot", "")
        app.setdefault("qr", "")
    for index, person in enumerate(report["staffList"]):
        person.setdefault("uid", f"staff-{index + 1}")
        person.setdefault("rank", "")
        person.setdefault("name", "")
        person.setdefault("role", "")
        person.setdefault("reason", "")
        for score in ("s1", "s2", "s3"):
            try:
                person[score] = int(person.get(score) or 0)
            except (TypeError, ValueError):
                person[score] = 0
    for index, item in enumerate(report["workshops"]):
        item.setdefault("uid", f"ws-{index + 1}")
        for field in ("title", "location", "speaker", "datetime", "target", "outcomes"):
            item.setdefault(field, "")
        item.setdefault("photos", [])
        _ensure_photos(item["photos"])
    for index, item in enumerate(report["seminars"]):
        item.setdefault("uid", f"sem-{index + 1}")
        for field in ("title", "date", "impact", "desc"):
            item.setdefault(field, "")
        item.setdefault("photos", [])
        _ensure_photos(item["photos"])
    clean_rows = []
    for row in report["comparisons"]:
        if isinstance(row, dict):
            clean_rows.append(
                {
                    "criterion": str(row.get("criterion") or ""),
                    "before": str(row.get("before") or ""),
                    "after": str(row.get("after") or ""),
                }
            )
    report["comparisons"] = clean_rows or default_report()["comparisons"]


def _ensure_photos(photos: list) -> None:
    for photo in photos:
        if isinstance(photo, dict):
            photo.setdefault("uid", _uid("pic"))
            photo.setdefault("src", "")
            photo.setdefault("caption", "")


def esc(value: object) -> str:
    return html.escape("" if value is None else str(value))


def br(value: object) -> str:
    return esc(value).replace("\n", "<br>")


def shape(value: object) -> str:
    text = "" if value is None else str(value)
    lines = []
    for line in text.split("\n"):
        lines.append(get_display(arabic_reshaper.reshape(line)) if line else "")
    return "\n".join(lines)


def file_to_data_url(uploaded) -> str:
    raw = uploaded.getvalue()
    mime = (getattr(uploaded, "type", "") or "").lower()
    if "svg" in mime:
        encoded = base64.b64encode(raw).decode("ascii")
        return f"data:image/svg+xml;base64,{encoded}"
    try:
        image = Image.open(io.BytesIO(raw))
        image = image.convert("RGB")
        image.thumbnail((1400, 1400))
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=82)
        encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
        return "data:image/jpeg;base64," + encoded
    except OSError:
        encoded = base64.b64encode(raw).decode("ascii")
        return f"data:{mime or 'image/jpeg'};base64,{encoded}"


def data_url_bytes(src: str) -> bytes:
    payload = src.split(",", 1)[1] if "," in src else src
    return base64.b64decode(payload)


def is_raster(src: str) -> bool:
    if not src or not src.startswith("data:image/"):
        return False
    header = src.split(",", 1)[0]
    return "svg" not in header


def bind_text(label: str, holder: dict, field: str, key: str, area: bool = False, **kwargs):
    if key not in st.session_state:
        st.session_state[key] = holder.get(field) or ""
    widget = st.text_area if area else st.text_input
    holder[field] = widget(label, key=key, **kwargs)


def bind_check(label: str, holder: dict, field: str, key: str) -> None:
    if key not in st.session_state:
        st.session_state[key] = bool(holder.get(field))
    holder[field] = st.checkbox(label, key=key)


def bind_score(label: str, holder: dict, field: str, key: str) -> None:
    if key not in st.session_state:
        try:
            st.session_state[key] = int(holder.get(field) or 0)
        except (TypeError, ValueError):
            st.session_state[key] = 0
    holder[field] = int(st.number_input(label, min_value=0, max_value=100, step=1, key=key))


def average(person: dict) -> float:
    return (int(person.get("s1") or 0) + int(person.get("s2") or 0) + int(person.get("s3") or 0)) / 3


def clear_widget_keys() -> None:
    for key in list(st.session_state.keys()):
        if str(key).startswith("tm_"):
            del st.session_state[key]


def logo_src(report: dict) -> str:
    return report.get("logo") or PERMANENT_LOGO


def render_banner() -> None:
    st.html(
        f"""
        <div class="top-banner">
          <div>
            <div class="kicker">المملكة العربية السعودية — وزارة الداخلية — الأمن العام</div>
            <h2>منصة تميّز | قسم مرور محافظة العارضة</h2>
            <div class="lede">توثيق ملف جائزة معالي مدير الأمن العام للانضباط السلوكي (هدفنا أمن وتواصل)</div>
          </div>
          <img src="{PERMANENT_LOGO}" alt="شعار المرور">
        </div>
        """
    )


def page_intro(title: str, lede: str) -> None:
    st.caption("قسم مرور محافظة العارضة")
    st.header(title)
    st.caption(lede)


def photo_editor(photos: list, owner: str) -> None:
    with st.form(f"tm_form_{owner}", clear_on_submit=True):
        uploads = st.file_uploader(
            "رفع الصور",
            type=["png", "jpg", "jpeg", "webp"],
            accept_multiple_files=True,
            key=f"tm_up_{owner}",
        )
        caption = st.text_input("تعليق يُطبَّق على الصور المحددة", key=f"tm_newcap_{owner}")
        submitted = st.form_submit_button("إضافة الصور", icon=":material/add_photo_alternate:", width="stretch")
    if submitted:
        if not uploads:
            st.warning("اختر صورة واحدة على الأقل.")
        else:
            for item in uploads:
                photos.append({"uid": _uid("pic"), "src": file_to_data_url(item), "caption": caption or "شاهد — قسم مرور محافظة العارضة"})
            st.rerun()
    if not photos:
        st.caption("لا توجد صور مرفقة بعد.")
        return
    for photo in list(photos):
        with st.container(border=True):
            left, right = st.columns([1, 3], vertical_alignment="center")
            with left:
                if photo.get("src"):
                    st.image(data_url_bytes(photo["src"]), width=150, alt=photo.get("caption") or "صورة مرفقة")
            with right:
                bind_text("التعليق", photo, "caption", f"tm_cap_{photo['uid']}")
                if st.button("حذف الصورة", key=f"tm_delpic_{photo['uid']}", icon=":material/delete:"):
                    photos.remove(photo)
                    st.rerun()


def single_image_field(holder: dict, field: str, label: str, owner: str) -> None:
    nonce_field = f"{field}_nonce"
    holder.setdefault(nonce_field, 0)
    uploaded = st.file_uploader(
        label,
        type=["png", "jpg", "jpeg", "webp"],
        key=f"tm_file_{owner}_{field}_{holder[nonce_field]}",
    )
    if uploaded is not None:
        holder[field] = file_to_data_url(uploaded)
    current = holder.get(field) or ""
    if current and is_raster(current):
        st.image(data_url_bytes(current), width=180, alt=label)
    if current and st.button("إزالة الصورة", key=f"tm_clr_{owner}_{field}"):
        holder[field] = ""
        holder[nonce_field] = int(holder.get(nonce_field) or 0) + 1
        st.rerun()


def render_cover(report: dict) -> None:
    page_intro("الغلاف والبيانات", "عنوان التقرير، التواريخ، الاعتماد، والملخص التنفيذي.")
    st.caption("الشعار الرسمي يُعرض تلقائياً من traffic_logo.png. ارفع صورة فقط إذا أردت استبداله في هذا التقرير.")
    if not report.get("logo") and LOGO_FILE.is_file():
        st.image(str(LOGO_FILE), width=120, alt="شعار المرور الرسمي")
    single_image_field(report, "logo", "شعار الأمن العام / المرور", "logo")
    bind_text("عنوان التقرير الرئيسي", report, "title", "tm_title", area=True, height=90)
    bind_text("العنوان الفرعي", report, "subtitle", "tm_subtitle")
    c1, c2 = st.columns(2)
    with c1:
        bind_text("التاريخ الهجري", report, "hijri", "tm_hijri")
        bind_text("رقم التقرير / المرجع", report, "ref", "tm_ref")
        bind_text("معد التقرير والمشرف التقني", report, "author", "tm_author")
    with c2:
        bind_text("التاريخ الميلادي", report, "greg", "tm_greg")
        bind_text("مدير القسم (الاعتماد)", report, "manager", "tm_manager")
        bind_text("القوة البشرية", report, "staffCount", "tm_staff_count")
    c3, c4, c5 = st.columns(3)
    with c3:
        bind_text("مؤشر الانضباط والقيافة", report, "discRate", "tm_disc")
    with c4:
        bind_text("الأنظمة الرقمية", report, "sysCount", "tm_sys")
    with c5:
        bind_text("المخالفات المسلكية", report, "violations", "tm_viol")
    bind_text("الملخص التنفيذي", report, "exec", "tm_exec", area=True, height=160)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("القوة البشرية", report["staffCount"])
    m2.metric("الانضباط", report["discRate"])
    m3.metric("الأنظمة", report["sysCount"])
    m4.metric("المخالفات المسلكية", report["violations"])


def render_axes(report: dict) -> None:
    page_intro("المحاور العشرة", "مصفوفة الجائزة قابلة للتعديل لتطابق صياغة التعميم، مع الشواهد والصور لكل محور.")
    bind_text("وصف الحوكمة والانضباط الإداري", report, "govText", "tm_gov", area=True, height=120)
    bind_text("تطبيق قيمة المسؤولية", report, "valText", "tm_val", area=True, height=120)
    axes = [axis for axis in report["axes"] if isinstance(axis, dict)]
    if not axes:
        st.info("لا توجد محاور في هذا الملف.", title="المحاور")
        return
    st.dataframe(
        [
            {
                "م": index + 1,
                "المحور": axis["name"],
                "المؤشر": axis["indicator"],
                "في التقرير": "نعم" if axis.get("enabled", True) else "لا",
            }
            for index, axis in enumerate(axes)
        ],
        width="stretch",
        hide_index=True,
        alt="ملخص المحاور العشرة ومؤشر كل محور",
    )
    index = st.selectbox(
        "تحرير المحور",
        list(range(len(axes))),
        format_func=lambda item: f"{item + 1}. {axes[item]['name']}",
        key="tm_axis_index",
    )
    axis = axes[int(index)]
    with st.container(border=True):
        bind_check("إظهار هذا المحور في التقرير", axis, "enabled", f"tm_ax_on_{axis['uid']}")
        bind_text("اسم المحور", axis, "name", f"tm_ax_name_{axis['uid']}")
        bind_text("الشعار المختصر", axis, "motto", f"tm_ax_motto_{axis['uid']}")
        bind_text("مؤشر القياس", axis, "indicator", f"tm_ax_ind_{axis['uid']}")
        bind_text("الشاهد والتطبيق في القسم", axis, "text", f"tm_ax_text_{axis['uid']}", area=True, height=140)
        photo_editor(axis["photos"], axis["uid"])


def render_apps(report: dict) -> None:
    page_intro("التطبيقات الذكية", "إدارة حسم ورقابة وبينة، أو أي مبادرة رقمية إضافية، مع لقطة الشاشة ورمز QR.")
    if st.button("إضافة تطبيق", icon=":material/add:", type="primary"):
        report["apps"].append(
            {
                "uid": _uid("app"),
                "name": "تطبيق رقمي جديد",
                "impact": "تعزيز الانضباط وجودة الأداء",
                "desc": "وصف المبادرة وأثرها على العمل المروري في القسم.",
                "screenshot": "",
                "qr": "",
            }
        )
        st.rerun()
    if not report["apps"]:
        st.info("أضف تطبيقاً ليظهر في محور التحول الرقمي.", title="لا توجد تطبيقات")
        return
    for app in list(report["apps"]):
        with st.container(border=True):
            st.subheader(app.get("name") or "تطبيق")
            bind_text("اسم التطبيق", app, "name", f"tm_app_name_{app['uid']}")
            bind_text("الارتباط بمعيار الجائزة", app, "impact", f"tm_app_impact_{app['uid']}")
            bind_text("الوصف", app, "desc", f"tm_app_desc_{app['uid']}", area=True, height=110)
            left, right = st.columns(2)
            with left:
                single_image_field(app, "screenshot", "صورة شاشة التطبيق", app["uid"] + "s")
            with right:
                single_image_field(app, "qr", "رمز QR", app["uid"] + "q")
            if st.button("حذف التطبيق", key=f"tm_del_app_{app['uid']}", icon=":material/delete:"):
                report["apps"].remove(app)
                st.rerun()


def render_staff(report: dict) -> None:
    page_intro("تقييم المتميزين", "ترشيح الأفراد وفق الانضباط السلوكي، وإتقان الواجب، والتفاعل مع الأنظمة الرقمية.")
    st.caption("أوزان المنهجية في التقرير: 40% انضباط، 30% إتقان الواجب، 20% الأنظمة الرقمية، 10% المبادرة والتواصل.")
    if st.button("إضافة مرشح", icon=":material/person_add:", type="primary"):
        report["staffList"].append(
            {
                "uid": _uid("staff"),
                "rank": "رقيب",
                "name": "اسم الفرد المتميز",
                "role": "مهام ميدانية",
                "s1": 100,
                "s2": 99,
                "s3": 98,
                "reason": "الالتزام بالقيافة وسرعة إنجاز المهام الميدانية.",
            }
        )
        st.rerun()
    for person in list(report["staffList"]):
        with st.container(border=True):
            st.subheader(person.get("name") or "مرشح")
            c1, c2 = st.columns(2)
            with c1:
                bind_text("الرتبة / الصفة", person, "rank", f"tm_st_rank_{person['uid']}")
            with c2:
                bind_text("الاسم", person, "name", f"tm_st_name_{person['uid']}")
            bind_text("المهمة في القسم", person, "role", f"tm_st_role_{person['uid']}")
            s1, s2, s3, avg = st.columns(4, vertical_alignment="bottom")
            with s1:
                bind_score("الانضباط السلوكي %", person, "s1", f"tm_st_s1_{person['uid']}")
            with s2:
                bind_score("إتقان الواجب %", person, "s2", f"tm_st_s2_{person['uid']}")
            with s3:
                bind_score("التفاعل التقني %", person, "s3", f"tm_st_s3_{person['uid']}")
            with avg:
                st.metric("المتوسط", f"{average(person):.1f}%")
            bind_text("مبررات التميز", person, "reason", f"tm_st_reason_{person['uid']}", area=True, height=90)
            if st.button("حذف المرشح", key=f"tm_del_st_{person['uid']}", icon=":material/delete:"):
                report["staffList"].remove(person)
                st.rerun()


def render_workshops(report: dict) -> None:
    page_intro("ورش العمل والاجتماعات", "توثيق الورشة: المكان، المتحدث، المخرجات، والصور.")
    if st.button("إضافة ورشة أو اجتماع", icon=":material/add:", type="primary"):
        report["workshops"].append(
            {
                "uid": _uid("ws"),
                "title": "اجتماع لتعزيز الانضباط السلوكي",
                "location": "مقر قسم مرور محافظة العارضة",
                "speaker": "مدير قسم مرور محافظة العارضة",
                "datetime": "١٤٤٨ هـ",
                "target": "أفراد قسم مرور محافظة العارضة",
                "outcomes": "مراجعة الانضباط الميداني ومعايير الجائزة.",
                "photos": [],
            }
        )
        st.rerun()
    for item in list(report["workshops"]):
        with st.container(border=True):
            bind_text("العنوان", item, "title", f"tm_ws_title_{item['uid']}")
            c1, c2 = st.columns(2)
            with c1:
                bind_text("الموقع", item, "location", f"tm_ws_loc_{item['uid']}")
            with c2:
                bind_text("الوقت والتاريخ", item, "datetime", f"tm_ws_dt_{item['uid']}")
            bind_text("المتحدث", item, "speaker", f"tm_ws_sp_{item['uid']}")
            bind_text("الحضور", item, "target", f"tm_ws_tg_{item['uid']}")
            bind_text("المخرجات", item, "outcomes", f"tm_ws_out_{item['uid']}", area=True, height=110)
            photo_editor(item["photos"], item["uid"])
            if st.button("حذف الورشة", key=f"tm_del_ws_{item['uid']}", icon=":material/delete:"):
                report["workshops"].remove(item)
                st.rerun()


def render_field(report: dict) -> None:
    page_intro("الميدان والندوات", "الجاهزية على طرق العارضة، والندوات والمبادرات مع صورها.")
    bind_text("جهود الانضباط الميداني", report, "fieldText", "tm_field", area=True, height=140)
    if st.button("إضافة ندوة أو مبادرة", icon=":material/add:", type="primary"):
        report["seminars"].append(
            {
                "uid": _uid("sem"),
                "title": "ندوة ميدانية جديدة",
                "date": "١٤٤٨ هـ",
                "impact": "تعزيز السلامة المرورية والتواصل المجتمعي",
                "desc": "وصف المبادرة التي نفذها قسم مرور محافظة العارضة.",
                "photos": [],
            }
        )
        st.rerun()
    for item in list(report["seminars"]):
        with st.container(border=True):
            bind_text("العنوان", item, "title", f"tm_sem_title_{item['uid']}")
            c1, c2 = st.columns(2)
            with c1:
                bind_text("التاريخ", item, "date", f"tm_sem_date_{item['uid']}")
            with c2:
                bind_text("الأثر", item, "impact", f"tm_sem_impact_{item['uid']}")
            bind_text("التفاصيل", item, "desc", f"tm_sem_desc_{item['uid']}", area=True, height=110)
            photo_editor(item["photos"], item["uid"])
            if st.button("حذف الندوة", key=f"tm_del_sem_{item['uid']}", icon=":material/delete:"):
                report["seminars"].remove(item)
                st.rerun()


def render_kpi(report: dict) -> None:
    page_intro("الأثر والاعتماد", "مقارنة قبل التحول الرقمي وبعده، ثم الميثاق والتوصيات والتوقيع.")
    st.caption("يمكن إضافة صفوف المقارنة أو حذفها من الجدول.")
    edited = st.data_editor(
        report["comparisons"],
        num_rows="dynamic",
        width="stretch",
        hide_index=True,
        key="tm_kpi_table",
        alt="جدول مقارنة الأثر قبل التحول الرقمي وبعده",
        column_config={
            "criterion": st.column_config.TextColumn("معيار القياس", required=True),
            "before": st.column_config.TextColumn("قبل"),
            "after": st.column_config.TextColumn("بعد"),
        },
    )
    report["comparisons"] = _records(edited)
    bind_text("ميثاق الانضباط السلوكي", report, "pledge", "tm_pledge", area=True, height=130)
    bind_text("التوصيات", report, "recommendations", "tm_reco", area=True, height=130)


def _records(value) -> list[dict]:
    if hasattr(value, "to_dict"):
        rows = value.to_dict("records")
    else:
        rows = list(value or [])
    cleaned = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        cleaned.append(
            {
                "criterion": "" if row.get("criterion") is None else str(row.get("criterion")),
                "before": "" if row.get("before") is None else str(row.get("before")),
                "after": "" if row.get("after") is None else str(row.get("after")),
            }
        )
    return [row for row in cleaned if any(row.values())]


def render_report_page(report: dict) -> None:
    page_intro("توليد التقرير", "معاينة A4، ثم الطباعة وحفظ PDF من المتصفح، أو تنزيل ملف PDF مباشرة.")
    document = build_report_html(report)
    with st.container(horizontal=True, vertical_alignment="center"):
        st.download_button(
            "تنزيل HTML للطباعة",
            data=document.encode("utf-8"),
            file_name="تقرير-تميز-مرور-العارضة.html",
            mime="text/html",
            icon=":material/html:",
            type="primary",
        )
        if st.button("توليد ملف PDF", icon=":material/picture_as_pdf:"):
            try:
                st.session_state["tm_pdf_bytes"] = build_report_pdf(report)
                st.session_state["flash"] = "تم توليد ملف PDF."
            except Exception as exc:
                st.session_state["tm_pdf_error"] = str(exc)
            st.rerun()
    if st.session_state.get("tm_pdf_error"):
        st.error(st.session_state.pop("tm_pdf_error"), title="تعذر إنشاء PDF")
    if st.session_state.get("tm_pdf_bytes"):
        st.download_button(
            "تنزيل PDF",
            data=st.session_state["tm_pdf_bytes"],
            file_name="تقرير-تميز-مرور-العارضة.pdf",
            mime="application/pdf",
            icon=":material/download:",
        )
    _print_button(document)
    st.caption("في نافذة الطباعة اختر حفظ كـ PDF وفعّل طباعة الخلفيات حتى تظهر الألوان الرسمية.")
    st.iframe(document, height=980, alt="معاينة تقرير تميز بمقاس A4")


def _print_button(document: str) -> None:
    payload = json.dumps(document).replace("<", "\\u003c")
    st.html(
        f"""
        <button id="tm-print" type="button" style="width:100%;min-height:46px;cursor:pointer;font-weight:700;border-radius:10px;border:1px solid #e7c98a;background:#0b4f26;color:#fff;font-family:Cairo,Tahoma,sans-serif;">
          طباعة التقرير أو حفظه PDF
        </button>
        <script>
          const docHtml = {payload};
          const button = document.getElementById("tm-print");
          button.addEventListener("click", () => {{
            const popup = window.open("", "tamayuzPrint", "popup,width=980,height=1200");
            if (!popup) return;
            popup.document.open();
            popup.document.write(docHtml);
            popup.document.close();
            setTimeout(() => popup.print(), 300);
          }});
        </script>
        """,
        unsafe_allow_javascript=True,
    )


def sidebar_nav(report: dict) -> None:
    with st.sidebar:
        st.html(
            """
            <div class="tm-brand">
              <h2>منصة تميّز</h2>
              <p>أقسام التحرير في التبويبات العلوية. من هنا تُظهر محاور التقرير وتحفظ الملف.</p>
            </div>
            """
        )
        st.markdown("**إظهار المحاور في التقرير**")
        bind_check("الحوكمة والقيم", report, "showGov", "tm_show_gov")
        bind_check("المحاور العشرة", report, "showAxes", "tm_show_axes")
        bind_check("التطبيقات الذكية", report, "showApps", "tm_show_apps")
        bind_check("تقييم المتميزين", report, "showStaff", "tm_show_staff")
        bind_check("ورش العمل", report, "showWorkshops", "tm_show_ws")
        bind_check("الميدان والندوات", report, "showField", "tm_show_field")
        bind_check("الأثر والاعتماد", report, "showKpi", "tm_show_kpi")


def render_workspace(report: dict) -> None:
    labels = [
        "📄 معاينة التقرير والطباعة",
        "⚙️ بيانات الغلاف والاعتماد",
        "💻 التطبيقات الذكية",
        "🏅 التقييم وورش العمل",
    ]
    preview, cover, apps, evaluation = st.tabs(labels, key="tm_sections", on_change="rerun")
    if preview.open:
        with preview:
            render_report_page(report)
    if cover.open:
        with cover:
            render_cover(report)
            st.divider()
            render_kpi(report)
    if apps.open:
        with apps:
            render_apps(report)
    if evaluation.open:
        with evaluation:
            render_axes(report)
            st.divider()
            render_staff(report)
            st.divider()
            render_workshops(report)
            st.divider()
            render_field(report)


def sidebar_tools(report: dict) -> None:
    with st.sidebar:
        st.divider()
        st.markdown("**حفظ البيانات واستعادتها**")
        st.download_button(
            "حفظ ملف JSON",
            data=json.dumps(report, ensure_ascii=False, indent=2).encode("utf-8"),
            file_name="تقرير-تميز.json",
            mime="application/json",
            icon=":material/save:",
            width="stretch",
        )
        uploaded = st.file_uploader("فتح ملف سابق", type=["json"], key="tm_import")
        if st.button("اعتماد الملف", icon=":material/folder_open:", width="stretch") and uploaded is not None:
            try:
                st.session_state["pending_import"] = json.loads(uploaded.getvalue().decode("utf-8"))
                st.session_state["flash"] = "تم فتح ملف التقرير."
                st.rerun()
            except (UnicodeDecodeError, json.JSONDecodeError):
                st.error("الملف غير صالح.")
        if st.button("استعادة الافتراضي", icon=":material/restart_alt:", width="stretch"):
            st.session_state["pending_reset"] = True
            st.rerun()
        st.caption("احفظ JSON قبل إغلاق الصفحة. جلسة المتصفح لا تُبقي الصور بعد التحديث.")
        st.caption("هدفنا أمن وتواصل")


def build_report_html(report: dict) -> str:
    pages = _html_pages(report)
    total = max(len(pages), 1)
    if not pages:
        pages = ["<p>فعّل محوراً واحداً على الأقل من الشريط الجانبي.</p>"]
    body = []
    for index, content in enumerate(pages, start=1):
        body.append(
            f"""
            <section class="report-page">
              <div class="page-inner">
                {_html_header(report)}
                {content}
              </div>
              {_html_footer(index, total)}
            </section>
            """
        )
    return _HTML_SHELL.replace("<!--BODY-->", "\n".join(body))


def _html_header(report: dict) -> str:
    return f"""
    <div class="official-header">
      <div class="header-right">
        المملكة العربية السعودية<br>وزارة الداخلية - الأمن العام<br>الإدارة العامة للمرور<br>
        إدارة مرور منطقة جازان<br><span class="gold">قسم مرور محافظة العارضة</span>
      </div>
      <div class="header-center"><img src="{logo_src(report)}" alt="شعار المرور"></div>
      <div class="header-left">
        الرقم المرجعي: {esc(report.get("ref"))}<br>
        التاريخ الهجري: {esc(report.get("hijri"))}<br>
        التاريخ الميلادي: {esc(report.get("greg"))}<br>
        شعار الجائزة: <strong>هدفنا أمن وتواصل</strong>
      </div>
    </div>
    """


def _html_footer(page: int, total: int) -> str:
    return f"""
    <div class="page-footer">
      <span>إدارة مرور منطقة جازان - قسم مرور محافظة العارضة</span>
      <span>جائزة معالي مدير الأمن العام للانضباط السلوكي</span>
      <span>صفحة {page} من {total}</span>
    </div>
    """


def _html_pages(report: dict) -> list[str]:
    pages: list[str] = [_cover_html(report)]
    if report.get("showGov"):
        pages.append(
            f"""
            <div class="sec-heading"><div>أولاً: الحوكمة والانضباط الإداري ومصفوفة القيم</div><span>المسؤولية</span></div>
            <table class="official-table">
              <thead><tr><th style="width:28%">المرتكز</th><th>التطبيق في قسم مرور العارضة</th></tr></thead>
              <tbody>
                <tr><td><strong>الحوكمة والانضباط اليومي</strong></td><td>{esc(report.get("govText"))}</td></tr>
                <tr><td><strong>قيمة المسؤولية</strong></td><td>{esc(report.get("valText"))}</td></tr>
              </tbody>
            </table>
            """
        )
    if report.get("showAxes"):
        visible = [axis for axis in report["axes"] if axis.get("enabled", True)]
        for chunk in _chunks(visible, 2):
            cards = []
            for axis in chunk:
                cards.append(
                    f"""
                    <article class="keep">
                      <div class="sec-heading"><div>{esc(axis.get("name"))}</div><span>{esc(axis.get("motto"))}</span></div>
                      <p class="body">{esc(axis.get("text"))}</p>
                      <p class="indicator">مؤشر القياس: {esc(axis.get("indicator"))}</p>
                      {_photos_html(axis.get("photos") or [])}
                    </article>
                    """
                )
            pages.append("".join(cards))
    if report.get("showApps") and report["apps"]:
        for chunk in _chunks(report["apps"], 3):
            cards = []
            for app in chunk:
                media = ""
                if app.get("screenshot"):
                    media += f'<img src="{app["screenshot"]}" class="app-shot" alt="واجهة التطبيق">'
                if app.get("qr"):
                    media += f'<img src="{app["qr"]}" class="app-qr" alt="رمز QR">'
                cards.append(
                    f"""
                    <div class="app-report-card keep">
                      <div>
                        <h4>{esc(app.get("name"))}</h4>
                        <span class="badge">{esc(app.get("impact"))}</span>
                        <p>{esc(app.get("desc"))}</p>
                      </div>
                      <div class="app-media">{media}</div>
                    </div>
                    """
                )
            pages.append(
                '<div class="sec-heading"><div>ثانياً: التحول الرقمي — حسم، رقابة، بينة</div><span>مبادرات القسم</span></div>'
                + "".join(cards)
            )
    if report.get("showStaff") and report["staffList"]:
        rows = []
        for index, person in enumerate(report["staffList"], start=1):
            rows.append(
                "<tr>"
                f"<td>{index}</td>"
                f"<td><strong>{esc(person.get('rank'))}</strong><br>{esc(person.get('name'))}</td>"
                f"<td>{esc(person.get('role'))}</td>"
                f"<td>{int(person.get('s1') or 0)}%</td>"
                f"<td>{int(person.get('s2') or 0)}%</td>"
                f"<td>{int(person.get('s3') or 0)}%</td>"
                f"<td><span class='pill'>{average(person):.1f}%</span></td>"
                f"<td>{esc(person.get('reason'))}</td>"
                "</tr>"
            )
        pages.append(
            """
            <div class="sec-heading"><div>ثالثاً: تقييم الأفراد المتميزين</div><span>لوحة الشرف</span></div>
            <table class="official-table staff">
              <thead><tr><th>م</th><th>الرتبة والاسم</th><th>المهمة</th><th>الانضباط</th><th>الإتقان</th><th>التقنية</th><th>المتوسط</th><th>المبررات</th></tr></thead>
              <tbody>
            """
            + "".join(rows)
            + """
              </tbody>
            </table>
            <div class="kpi-row">
              <div><b>40%</b><span>الانضباط العسكري والقيافة</span></div>
              <div><b>30%</b><span>إتقان الواجب وسرعة الإنجاز</span></div>
              <div><b>20%</b><span>تطبيق حسم ورقابة وبينة</span></div>
              <div><b>10%</b><span>المبادرة والتواصل</span></div>
            </div>
            """
        )
    if report.get("showWorkshops"):
        for number, item in enumerate(report["workshops"], start=1):
            photos = item.get("photos") or []
            pages.append(
                f"""
                <div class="sec-heading"><div>رابعاً: ورش العمل والاجتماعات ({number})</div><span>تثقيف الأفراد</span></div>
                <table class="official-table">
                  <tbody>
                    <tr><th>العنوان</th><td>{esc(item.get("title"))}</td></tr>
                    <tr><th>الموقع</th><td>{esc(item.get("location"))}</td></tr>
                    <tr><th>المتحدث</th><td>{esc(item.get("speaker"))}</td></tr>
                    <tr><th>الوقت</th><td>{esc(item.get("datetime"))}</td></tr>
                    <tr><th>الحضور</th><td>{esc(item.get("target"))}</td></tr>
                    <tr><th>المخرجات</th><td>{esc(item.get("outcomes"))}</td></tr>
                  </tbody>
                </table>
                {_photos_html(photos[:4])}
                """
            )
            for extra in _chunks(photos[4:], 4):
                pages.append(_photos_html(extra))
    if report.get("showField"):
        seminar_html = []
        for item in report["seminars"]:
            seminar_html.append(
                f"""
                <table class="official-table keep">
                  <thead><tr><th colspan="2">{esc(item.get("title"))} ({esc(item.get("date"))})</th></tr></thead>
                  <tbody>
                    <tr><td><strong>الأثر</strong></td><td>{esc(item.get("impact"))}</td></tr>
                    <tr><td><strong>التفاصيل</strong></td><td>{esc(item.get("desc"))}</td></tr>
                  </tbody>
                </table>
                {_photos_html(item.get("photos") or [])}
                """
            )
        pages.append(
            f"""
            <div class="sec-heading"><div>خامساً: الانضباط الميداني والندوات</div><span>هدفنا أمن وتواصل</span></div>
            <div class="note"><h3>الجاهزية في محافظة العارضة</h3><p>{esc(report.get("fieldText"))}</p></div>
            {''.join(seminar_html)}
            """
        )
    if report.get("showKpi"):
        rows = []
        for row in report.get("comparisons") or []:
            rows.append(
                "<tr>"
                f"<td><strong>{esc(row.get('criterion'))}</strong></td>"
                f"<td>{esc(row.get('before'))}</td>"
                f"<td>{esc(row.get('after'))}</td>"
                "</tr>"
            )
        pages.append(
            f"""
            <div class="sec-heading"><div>سادساً: مؤشرات الأثر</div><span>قبل / بعد</span></div>
            <table class="official-table">
              <thead><tr><th>المعيار</th><th>قبل</th><th>بعد تفعيل المنظومات والورش</th></tr></thead>
              <tbody>{''.join(rows)}</tbody>
            </table>
            <div class="sec-heading"><div>سابعاً: الميثاق والاعتماد</div><span>ختام التقرير</span></div>
            <div class="note"><h3>ميثاق الانضباط السلوكي</h3><p>{br(report.get("pledge"))}</p></div>
            <div class="note green"><h3>التوصيات</h3><p>{br(report.get("recommendations"))}</p></div>
            <table class="official-table">
              <thead><tr><th>إعداد التقرير</th><th>اعتماد مدير القسم</th></tr></thead>
              <tbody><tr>
                <td class="sign"><strong>{esc(report.get("author"))}</strong><br><br>التوقيع: ........................</td>
                <td class="sign"><strong>{esc(report.get("manager"))}</strong><br><br>التوقيع والختم: ........................</td>
              </tr></tbody>
            </table>
            """
        )
    return pages


def _photos_html(photos: list) -> str:
    valid = [photo for photo in photos if photo.get("src")]
    if not valid:
        return ""
    frames = []
    for photo in valid:
        frames.append(
            f"""
            <figure class="photo">
              <img src="{photo['src']}" alt="{esc(photo.get('caption') or 'شاهد')}">
              <figcaption>{esc(photo.get('caption'))}</figcaption>
            </figure>
            """
        )
    return f'<div class="photos">{"".join(frames)}</div>'


def _cover_html(report: dict) -> str:
    return f"""
    <div class="cover">
      <div class="badge">وثيقة رسمية | جائزة معالي مدير الأمن العام للانضباط السلوكي</div>
      <div class="title-frame">
        <h2>{esc(report.get("title"))}</h2>
        <p>{esc(report.get("subtitle"))}</p>
      </div>
      <div class="note"><h3>الملخص التنفيذي</h3><p>{br(report.get("exec"))}</p></div>
      <div class="kpi-row">
        <div><b>{esc(report.get("staffCount"))}</b><span>القوة البشرية</span></div>
        <div><b>{esc(report.get("discRate"))}</b><span>الانضباط والقيافة</span></div>
        <div><b>{esc(report.get("sysCount"))}</b><span>التحول الرقمي</span></div>
        <div><b>{esc(report.get("violations"))}</b><span>المخالفات المسلكية</span></div>
      </div>
      <div class="signs">
        <div><span>إعداد وإشراف المبادرات الرقمية</span><strong>{esc(report.get("author"))}</strong></div>
        <div><span>اعتماد مدير قسم مرور محافظة العارضة</span><strong>{esc(report.get("manager"))}</strong></div>
      </div>
    </div>
    """


def _chunks(items: list, size: int) -> list[list]:
    if not items:
        return []
    return [items[index : index + size] for index in range(0, len(items), size)]


_HTML_SHELL = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="utf-8">
  <title>تقرير تميّز | مرور محافظة العارضة</title>
  <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800;900&display=swap" rel="stylesheet">
  <style>
    :root { --green:#0b4f26; --deep:#073519; --gold:#c5a059; --cream:#f5ebd6; --ink:#1e293b; }
    * { box-sizing: border-box; }
    body { margin:0; background:#cbd5e1; color:var(--ink); font-family:"Cairo",Tahoma,sans-serif; }
    .report-page {
      width:210mm; min-height:297mm; margin:8mm auto; background:#fff; position:relative;
      padding:16mm 14mm 18mm; display:flex; flex-direction:column; justify-content:space-between;
      box-shadow:0 8px 24px rgba(0,0,0,.18); page-break-after:always; break-after:page;
    }
    .report-page:last-child { page-break-after:auto; break-after:auto; }
    .page-inner { position:relative; z-index:2; }
    .report-page::before, .report-page::after {
      content:""; position:absolute; pointer-events:none;
    }
    .report-page::before { inset:7mm; border:2px solid var(--green); }
    .report-page::after { inset:9mm; border:1px solid var(--gold); }
    .official-header { display:grid; grid-template-columns:1.3fr .8fr 1.3fr; gap:8px; align-items:center; border-bottom:3px double var(--gold); padding-bottom:8px; margin-bottom:12px; }
    .header-right { font-size:12px; font-weight:800; line-height:1.55; color:var(--deep); }
    .header-left { text-align:left; font-size:11px; font-weight:700; line-height:1.6; }
    .header-center { text-align:center; }
    .header-center img { height:68px; object-fit:contain; }
    .gold { color:var(--gold); }
    .cover { text-align:center; }
    .badge { display:inline-block; background:var(--cream); color:var(--deep); border:1px solid var(--gold); border-radius:30px; padding:6px 16px; font-weight:800; font-size:13px; }
    .title-frame { background:linear-gradient(135deg,var(--deep),var(--green)); color:#fff; border:3px solid var(--gold); border-radius:12px; padding:22px 18px; margin:12px 0; }
    .title-frame h2 { margin:0 0 8px; font-size:20px; line-height:1.55; color:#fff; }
    .title-frame p { margin:0; color:#f5ebd6; font-weight:700; }
    .note { text-align:right; background:#f8fafc; border-right:5px solid var(--gold); border:1px solid #e2e8f0; border-right-width:5px; border-radius:8px; padding:12px 14px; margin:10px 0; }
    .note.green { border-right-color:var(--green); }
    .note h3 { margin:0 0 6px; color:var(--deep); font-size:15px; }
    .note p, .body { margin:0; font-size:13px; line-height:1.75; text-align:justify; }
    .kpi-row, .signs { display:grid; grid-template-columns:repeat(4,1fr); gap:8px; margin-top:10px; }
    .signs { grid-template-columns:1fr 1fr; }
    .kpi-row div, .signs div { border:1px solid #cbd5e1; border-top:3px solid var(--green); border-radius:8px; padding:8px; text-align:center; background:#fff; }
    .kpi-row b, .signs strong { display:block; color:var(--deep); font-size:16px; }
    .kpi-row span, .signs span { display:block; color:#475569; font-size:11px; font-weight:700; }
    .sec-heading { display:flex; justify-content:space-between; gap:8px; align-items:center; background:linear-gradient(90deg,var(--deep),var(--green)); color:#fff; border-right:6px solid var(--gold); border-radius:4px; padding:7px 12px; margin:8px 0; font-weight:800; }
    .sec-heading span { color:#f5ebd6; font-size:11px; font-weight:600; }
    .indicator { margin:4px 0 8px; font-size:12px; font-weight:800; color:var(--deep); }
    .official-table { width:100%; border-collapse:collapse; margin:8px 0 12px; font-size:12px; }
    .official-table th { background:var(--deep); color:#fff; padding:6px; border:1px solid var(--deep); text-align:right; }
    .official-table td { padding:6px; border:1px solid #cbd5e1; vertical-align:top; }
    .official-table.staff { font-size:10px; }
    .staff td, .staff th { text-align:center; }
    .pill { background:var(--green); color:#fff; border-radius:12px; padding:2px 6px; font-weight:800; }
    .app-report-card { display:grid; grid-template-columns:1fr auto; gap:10px; border:1px solid #cbd5e1; border-right:5px solid var(--green); border-radius:8px; padding:10px; margin-bottom:8px; }
    .app-report-card h4 { margin:0 0 4px; color:var(--deep); }
    .badge { background:var(--cream); color:var(--deep); border-radius:4px; padding:2px 6px; font-size:11px; font-weight:700; }
    .app-media { display:flex; gap:6px; align-items:center; }
    .app-shot { width:95px; height:70px; object-fit:cover; border:1px solid var(--gold); border-radius:6px; }
    .app-qr { width:64px; height:64px; object-fit:contain; border:1px solid #cbd5e1; }
    .photos { display:grid; grid-template-columns:1fr 1fr; gap:8px; margin:8px 0; }
    .photo { margin:0; border:1px solid var(--gold); border-radius:6px; overflow:hidden; break-inside:avoid; }
    .photo img { width:100%; height:145px; object-fit:cover; display:block; }
    .photo figcaption { background:var(--cream); text-align:center; font-size:11px; font-weight:700; padding:4px 6px; }
    .sign { text-align:center; padding:16px 8px; }
    .page-footer { border-top:2px solid var(--gold); margin-top:12px; padding-top:6px; display:flex; justify-content:space-between; font-size:11px; font-weight:700; color:#475569; position:relative; z-index:2; }
    .keep { break-inside:avoid; page-break-inside:avoid; }
    @media print {
      @page { size:A4 portrait; margin:0; }
      body { background:#fff; }
      .report-page { margin:0; box-shadow:none; }
    }
  </style>
</head>
<body>
<!--BODY-->
</body>
</html>
"""


class ReportPDF(FPDF):
    def header(self):
        self.set_fill_color(7, 53, 25)
        self.rect(0, 0, 210, 7, "F")
        self.set_xy(12, 9)
        self.set_font("Naskh", "B", 11)
        self.set_text_color(7, 53, 25)
        self.cell(self.epw, 7, shape("قسم مرور محافظة العارضة — جائزة معالي مدير الأمن العام"), align="C")
        self.set_draw_color(197, 160, 89)
        self.set_line_width(0.45)
        self.line(12, 18, 198, 18)
        self.set_xy(self.l_margin, 22)

    def footer(self):
        self.set_y(-14)
        self.set_draw_color(197, 160, 89)
        self.line(12, self.get_y(), 198, self.get_y())
        self.set_y(-12)
        self.set_font("Naskh", "", 9)
        self.set_text_color(71, 85, 105)
        self.cell(self.epw / 2, 8, f"{self.page_no()} / {{nb}}", align="L")
        self.cell(self.epw / 2, 8, shape("هدفنا أمن وتواصل"), align="R")


def build_report_pdf(report: dict) -> bytes:
    if not FONT_REG.is_file() or not FONT_BOLD.is_file() or not FONT_LATIN.is_file():
        raise FileNotFoundError("خطوط التقرير غير موجودة داخل مجلد fonts.")
    pdf = ReportPDF()
    pdf.add_font("Naskh", "", str(FONT_REG))
    pdf.add_font("Naskh", "B", str(FONT_BOLD))
    pdf.add_font("NotoSans", "", str(FONT_LATIN))
    pdf.add_font("NotoSans", "B", str(FONT_LATIN_BOLD))
    pdf.set_fallback_fonts(["NotoSans"], exact_match=False)
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.alias_nb_pages()
    pdf.set_margins(12, 22, 12)
    pdf.add_page()
    _pdf_title(pdf, report.get("title") or "تقرير تميّز")
    _pdf_paragraph(pdf, report.get("subtitle") or "")
    _pdf_paragraph(pdf, f"المرجع: {report.get('ref', '')} | {report.get('hijri', '')} | {report.get('greg', '')}")
    _pdf_heading(pdf, "الملخص التنفيذي")
    _pdf_paragraph(pdf, report.get("exec") or "")
    _pdf_paragraph(
        pdf,
        f"القوة: {report.get('staffCount', '')} | الانضباط: {report.get('discRate', '')} | "
        f"الأنظمة: {report.get('sysCount', '')} | المخالفات: {report.get('violations', '')}",
    )
    if report.get("showGov"):
        _pdf_heading(pdf, "الحوكمة وقيمة المسؤولية")
        _pdf_paragraph(pdf, report.get("govText") or "")
        _pdf_paragraph(pdf, report.get("valText") or "")
    if report.get("showAxes"):
        _pdf_heading(pdf, "المحاور العشرة")
        for number, axis in enumerate(report["axes"], start=1):
            if not axis.get("enabled", True):
                continue
            _pdf_heading(pdf, f"{number}. {axis.get('name', '')}")
            _pdf_paragraph(pdf, axis.get("motto") or "")
            _pdf_paragraph(pdf, axis.get("text") or "")
            _pdf_paragraph(pdf, f"المؤشر: {axis.get('indicator', '')}")
            _pdf_photos(pdf, axis.get("photos") or [])
    if report.get("showApps"):
        _pdf_heading(pdf, "التطبيقات الذكية")
        for app in report["apps"]:
            _pdf_heading(pdf, app.get("name") or "تطبيق")
            _pdf_paragraph(pdf, app.get("impact") or "")
            _pdf_paragraph(pdf, app.get("desc") or "")
            for field in ("screenshot", "qr"):
                _pdf_image(pdf, app.get(field) or "", 42 if field == "qr" else 70)
    if report.get("showStaff"):
        _pdf_heading(pdf, "تقييم المتميزين")
        for person in report["staffList"]:
            _pdf_paragraph(
                pdf,
                f"{person.get('rank', '')} / {person.get('name', '')} — {person.get('role', '')}\n"
                f"الانضباط {person.get('s1', 0)}% | الإتقان {person.get('s2', 0)}% | "
                f"التقنية {person.get('s3', 0)}% | المتوسط {average(person):.1f}%\n"
                f"{person.get('reason', '')}",
            )
    if report.get("showWorkshops"):
        _pdf_heading(pdf, "ورش العمل والاجتماعات")
        for item in report["workshops"]:
            _pdf_paragraph(
                pdf,
                f"{item.get('title', '')}\nالموقع: {item.get('location', '')}\n"
                f"المتحدث: {item.get('speaker', '')}\nالوقت: {item.get('datetime', '')}\n"
                f"الحضور: {item.get('target', '')}\nالمخرجات: {item.get('outcomes', '')}",
            )
            _pdf_photos(pdf, item.get("photos") or [])
    if report.get("showField"):
        _pdf_heading(pdf, "الميدان والندوات")
        _pdf_paragraph(pdf, report.get("fieldText") or "")
        for item in report["seminars"]:
            _pdf_paragraph(pdf, f"{item.get('title', '')} ({item.get('date', '')})\n{item.get('impact', '')}\n{item.get('desc', '')}")
            _pdf_photos(pdf, item.get("photos") or [])
    if report.get("showKpi"):
        _pdf_heading(pdf, "مؤشرات الأثر")
        for row in report.get("comparisons") or []:
            _pdf_paragraph(pdf, f"{row.get('criterion', '')}\nقبل: {row.get('before', '')}\nبعد: {row.get('after', '')}")
        _pdf_heading(pdf, "الميثاق والتوصيات")
        _pdf_paragraph(pdf, report.get("pledge") or "")
        _pdf_paragraph(pdf, report.get("recommendations") or "")
        _pdf_paragraph(pdf, f"إعداد: {report.get('author', '')}")
        _pdf_paragraph(pdf, f"اعتماد: {report.get('manager', '')}")
    return bytes(pdf.output())


def _pdf_title(pdf: FPDF, text: str) -> None:
    pdf.set_x(pdf.l_margin)
    pdf.set_font("Naskh", "B", 14)
    pdf.set_text_color(7, 53, 25)
    pdf.multi_cell(0, 8, shape(text), align="R")
    pdf.ln(1)


def _pdf_heading(pdf: FPDF, text: str) -> None:
    if pdf.get_y() > 255:
        pdf.add_page()
    pdf.ln(1)
    pdf.set_x(pdf.l_margin)
    pdf.set_fill_color(7, 53, 25)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Naskh", "B", 12)
    pdf.multi_cell(0, 8, shape(text), align="R", fill=True)
    pdf.ln(1)


def _pdf_paragraph(pdf: FPDF, text: str) -> None:
    if not text:
        return
    pdf.set_x(pdf.l_margin)
    pdf.set_text_color(30, 41, 59)
    pdf.set_font("Naskh", "", 11)
    pdf.multi_cell(0, 7, shape(text), align="R")
    pdf.ln(1)


def _pdf_photos(pdf: FPDF, photos: list) -> None:
    for photo in photos:
        _pdf_image(pdf, photo.get("src") or "", 75)
        if photo.get("caption"):
            _pdf_paragraph(pdf, photo["caption"])


def _pdf_image(pdf: FPDF, src: str, width: float) -> None:
    if not is_raster(src):
        return
    if pdf.get_y() > 230:
        pdf.add_page()
    try:
        image = Image.open(io.BytesIO(data_url_bytes(src))).convert("RGB")
        image.thumbnail((1000, 1000))
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=80)
        buffer.seek(0)
        pdf.image(buffer, x=pdf.l_margin, w=width)
        pdf.ln(2)
    except (OSError, ValueError):
        return


def main() -> None:
    st.set_page_config(
        page_title="منصة تميّز | مرور محافظة العارضة",
        page_icon="🏅",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    st.html(APP_CSS)
    st.markdown(MOBILE_CSS, unsafe_allow_html=True)
    if "report" not in st.session_state:
        st.session_state.report = default_report()
    if "pending_import" in st.session_state:
        st.session_state.report = normalize(st.session_state.pop("pending_import"))
        clear_widget_keys()
    if st.session_state.pop("pending_reset", False):
        st.session_state.report = default_report()
        clear_widget_keys()
        st.session_state["flash"] = "تمت استعادة البيانات الافتراضية."
    report = st.session_state.report
    ensure_report(report)
    if flash := st.session_state.pop("flash", None):
        st.success(flash)
    render_banner()
    sidebar_nav(report)
    render_workspace(report)
    sidebar_tools(report)


if __name__ == "__main__":
    main()
