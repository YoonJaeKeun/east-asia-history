#!/usr/bin/env python3
"""Build an annotated A4 PDF containing chapters 1–11 of The Tale of Genji."""

import html
import re
import subprocess
import tempfile
from pathlib import Path

import markdown


BASE = Path(__file__).resolve().parent
SOURCE_DIR = BASE / "genji-complete"
OUTPUT = SOURCE_DIR / "겐지 이야기 제1-11첩.pdf"
CHAPTERS = [
    ("제1첩", "기리쓰보", "桐壺", "01-kiritsubo.md"),
    ("제2첩", "하하키기", "帚木", "02-hahakigi.md"),
    ("제3첩", "우쓰세미", "空蝉", "03-utsusemi.md"),
    ("제4첩", "유가오", "夕顔", "04-yugao.md"),
    ("제5첩", "와카무라사키", "若紫", "05-wakamurasaki.md"),
    ("제6첩", "스에쓰무하나", "末摘花", "06-suetsumuhana.md"),
    ("제7첩", "모미지노가", "紅葉賀", "07-momijinoga.md"),
    ("제8첩", "하나노엔", "花宴", "08-hananoen.md"),
    ("제9첩", "아오이", "葵", "09-aoi.md"),
    ("제10첩", "사카키", "賢木", "10-sakaki.md"),
    ("제11첩", "하나치루사토", "花散里", "11-hanachirusato.md"),
]
LOCAL_IMAGES = {
    "01-kiritsubo.md": "assets/01-kiritsubo.jpg",
    "02-hahakigi.md": "assets/02-hahakigi.jpg",
    "03-utsusemi.md": "assets/03-utsusemi.jpg",
}

# Notes are attached to the first occurrence that needs explanation.  Longer
# phrases are used where a short term (for example, "발") could also occur as
# part of an unrelated Korean word.
FOOTNOTES = {
    "01-kiritsubo.md": [
        ("여어니", "여어(女御): 천황의 후궁 가운데 높은 지위. 대개 황족이나 대신 가문의 딸이 책봉되었다."),
        ("갱의니", "갱(更衣): 여어보다 아래에 놓인 후궁의 지위. 이 작품에서는 겐지의 어머니가 이 지위로 입궁한다."),
        ("전상인들은", "전상인(殿上人): 천황의 생활 공간인 청량전 전상간에 오를 자격을 받은 귀족과 관인."),
        ("마외역의 비극", "마외역의 비극: 당 현종이 반란군의 압박을 받아 총희 양귀비를 죽게 한 사건. 지나친 총애가 나라를 어지럽힌 사례로 인용된다."),
        ("대납언은", "대납언(大納言): 태정관에서 대신 다음가는 고위 관직. 천황을 보좌하고 조정의 정무에 참여했다."),
        ("우대신의 딸", "우대신(右大臣): 태정관의 최고위 대신 가운데 하나로, 통상 좌대신 다음가는 자리."),
        ("동궁으로", "동궁(東宮): 본래 황태자의 궁을 뜻하며, 여기서는 황태자 자신을 가리킨다."),
        ("기리쓰보였다", "기리쓰보(桐壺): 궁성 안쪽인 내리(內裏)의 동북쪽에 있던 후궁 처소. 정식 명칭은 숙경사이며 뜰에 오동나무가 있어 이렇게 불렸다."),
        ("여방들의", "여방(女房): 귀족이나 후궁의 처소에서 시중과 문서·교양 업무를 맡은 여성. 단순한 하녀와는 지위와 역할이 달랐다."),
        ("청량전에", "청량전(清涼殿): 헤이안 궁궐에서 천황이 일상생활과 정무를 보던 중심 건물."),
        ("후량전에", "후량전(後涼殿): 청량전 서쪽에 붙어 있던 건물. 본래 천황의 물품을 두었으나 후궁의 거처로도 쓰였다."),
        ("하카마기 의식", "하카마기(袴着): 어린아이에게 처음 하카마를 입히며 성장을 축하하던 의식. 대개 서너 살 무렵 치렀다."),
        ("종삼위가", "종삼위(従三位): 일본 율령제의 높은 품계. 이 등급 이상은 공경의 반열에 들었다."),
        ("선명을", "선명(宣命): 천황의 뜻을 공식적으로 선포하는 문서 또는 그것을 낭독하는 말."),
        ("유게이노 묘부", "묘부(命婦): 일정한 품계를 지녔거나 고위 관인과 연계된 상급 여관을 부르는 칭호."),
        ("「장한가」", "《장한가(長恨歌)》: 당 현종과 양귀비의 사랑과 이별을 노래한 백거이의 장편 서사시."),
        ("비익조, 땅에서는 연리지", "비익조·연리지: 각각 한쪽 눈과 날개를 함께 써야 나는 새, 서로 가지가 맞붙은 나무. 떨어질 수 없는 부부나 연인의 비유다."),
        ("우근위부 관리", "우근위부(右近衛府): 궁궐 경비와 천황 호위를 맡은 근위 조직의 하나."),
        ("고로칸으로", "고로칸(鴻臚館): 외국 사절을 맞아 머물게 하던 관영 영빈 시설."),
        ("우대변의 아들", "우대변(右大弁): 여러 관청의 문서와 행정을 감독한 변관 조직의 고위 실무 관직."),
        ("미나모토 성을", "미나모토(源): 황족을 신하의 신분으로 내릴 때 내리던 대표적인 성. 여기서 ‘겐지’는 미나모토씨를 뜻한다."),
        ("미야스도코로를", "미야스도코로(御息所): 천황이나 황태자의 배우자를 높여 부르던 말. 작품에서는 황자·황녀의 어머니를 가리키는 경우가 많다."),
        ("병부경 친왕", "병부경(兵部卿): 군사 행정과 무관 인사를 맡은 병부성의 장관. 여기서는 친왕이 겸임한 관직이다."),
        ("원복을", "원복(元服): 소년이 머리 모양과 복식을 성인식에 맞게 바꾸고 관을 쓰는 남성 성인식."),
        ("자진전에서", "자진전(紫宸殿): 헤이안 궁궐의 국가적 의식과 공식 행사가 열린 정전."),
        ("가관역을", "가관역(加冠役): 원복식에서 소년의 머리에 성인의 관을 씌워 주는 주례자."),
        ("오우치기와", "오우치기(大袿): 귀족 여성의 격식 있는 겉옷인 우치기 가운데 특히 크고 품위 있게 만든 옷."),
        ("구로도도코로의", "구로도도코로(蔵人所): 천황의 명령 전달, 기밀 문서와 궁중 실무를 맡은 비서 기관."),
        ("관백이 될", "관백(関白): 성년 천황을 보좌하며 정무를 대신 처리한 최고위 직책."),
        ("구로도노쇼쇼는", "구로도노쇼쇼(蔵人少将): 천황의 측근인 구로도와 근위부의 소장을 겸한 젊은 고위 관인."),
        ("수리직과 다쿠미료", "수리직·다쿠미료: 궁궐과 관청의 수리·건축 및 각종 제작을 담당한 관청들."),
        ("니조원이다", "니조원(二条院): 헤이안쿄 니조 일대에 마련된 겐지의 저택. 이후 이야기의 주요 무대가 된다."),
    ],
    "02-hahakigi.md": [
        ("가타노 소장", "가타노 소장(交野少将): 당대 설화에 등장하는 호색한 귀공자. 수많은 연애를 벌인 인물의 전형으로 언급된다."),
        ("중장으로", "중장(中将): 궁궐 수비와 천황 호위를 맡은 근위부의 차관급 무관. 젊은 귀족이 선망하던 요직이었다."),
        ("도노추조는", "도노추조(頭中将): ‘구로도노토와 중장을 겸한 사람’이라는 관직명에서 온 통칭. 좌대신의 아들이며 아오이노우에의 오빠다."),
        ("사마노카미와", "사마노카미(左馬頭): 조정의 말과 마구를 관리한 좌마료의 장관."),
        ("도시키부노조가", "도시키부노조(藤式部丞): ‘후지와라씨 출신의 식부성 판관’이라는 뜻의 관직형 호칭."),
        ("수령들 사이", "수령(受領): 중앙에서 지방으로 내려가 한 나라의 행정을 실질적으로 담당한 지방관."),
        ("참의까지는", "참의(参議): 태정관의 정무 회의에 참여한 고위 관직. 공경 반열에 드는 기준으로 여겨졌다."),
        ("나오시만", "나오시(直衣): 헤이안 시대 고위 남성 귀족의 평상복. 정식 조복보다 자유롭지만 궁중에서도 입을 수 있었다."),
        ("가모 임시제", "가모 임시제(賀茂臨時祭): 교토 가모 신사에서 겨울에 거행한 임시 제례. 궁중 음악과 춤이 따랐다."),
        ("문장생이었을", "문장생(文章生): 대학료에서 한문학과 역사 등을 공부하며 관료 진출을 준비한 학생."),
        ("방위막이를", "방위막이(方違え): 음양도의 방위 금기를 피하려고 목적지와 다른 곳에서 하룻밤을 묵은 관습."),
        ("나카가미가 있는 방위", "나카가미(中神): 일정한 주기로 방향을 옮긴다고 여긴 금기의 신. 그 신이 있는 방향으로 이동하는 일을 꺼렸다."),
        ("기이노카미의 집", "기이노카미(紀伊守): 기이국의 장관을 뜻하는 관직명. 작품 속 인물은 관직으로 불리며 우쓰세미의 의붓아들이다."),
        ("이요노스케의 아들", "이요노스케(伊予介): 이요국 지방관의 차관. 우쓰세미의 남편이며 고기미의 의붓아버지다."),
    ],
    "03-utsusemi.md": [
        ("가까운 발 옆", "발(御簾): 가는 대나무나 갈대를 엮어 만든 가리개. 귀족 여성의 모습을 외부 남성에게 감추는 경계 역할을 했다."),
        ("고우치기 같은 옷", "고우치기(小袿): 귀족 여성이 평상시에 겉에 걸쳐 입던 짧고 편한 겉옷."),
        ("붉은 하카마", "하카마(袴): 허리 아래에 입는 통 넓은 바지 형태의 옷. 헤이안 귀족 여성은 흔히 붉은색을 착용했다."),
        ("우쓰세미", "우쓰세미(空蝉): 매미가 벗어 놓은 허물. 덧없는 현세를 뜻하기도 하며, 겐지를 피해 옷만 남기고 사라진 여인의 통칭이 된다."),
    ],
    "04-yugao.md": [
        ("다이니 유모", "다이니 유모(大弐乳母): 겐지의 유모. 남편의 관직인 다자이후 차관 ‘다이니’를 따라 부른 호칭이다."),
        ("아자리", "아자리(阿闍梨): 불교 의식과 수행을 지도할 자격을 인정받은 고승의 칭호."),
        ("구품연대", "구품연대(九品蓮台): 극락왕생하는 이를 근기에 따라 아홉 등급의 연꽃 자리로 맞는다는 정토교의 관념."),
        ("가리기누", "가리기누(狩衣): 본래 사냥복에서 유래해 헤이안 귀족 남성의 편한 평상복이 된 옷."),
        ("도리베노", "도리베노(鳥辺野): 헤이안쿄 동쪽의 장례·화장지. 당시 대표적인 묘지 공간이었다."),
        ("사십구재", "사십구재: 사람이 죽은 뒤 49일 동안 칠일마다 올리는 불교 의례. 마지막 49일째 심판 뒤 다음 생이 정해진다고 여겼다."),
    ],
    "05-wakamurasaki.md": [
        ("학질", "학질: 일정한 간격으로 오한과 고열이 되풀이되는 병. 오늘날의 말라리아와 비슷한 증상으로 이해된다."),
        ("북산", "북산(北山): 헤이안쿄 북쪽 산지. 사찰과 수행자의 암자가 많아 요양과 기도를 위해 찾던 곳이다."),
        ("시키부쿄 친왕", "시키부쿄 친왕(式部卿親王): 황족의 교육·의례와 인사를 맡은 식부성의 장관을 겸한 친왕. 무라사키의 아버지다."),
        ("쇼나곤", "쇼나곤(少納言): 본래 태정관의 관직명. 여기서는 그 관직명으로 불리는 무라사키의 유모 겸 여방."),
        ("독고를", "독고(独鈷): 양 끝이 뾰족한 금강저의 한 종류. 밀교 의식에서 번뇌를 깨뜨리는 법구로 사용한다."),
    ],
    "06-suetsumuhana.md": [
        ("히타치 친왕", "히타치 친왕(常陸宮): 히타치국과 관련된 명칭으로 불리는 황족. 스에쓰무하나의 아버지다."),
        ("다이후노묘부", "다이후노묘부(大輔命婦): 관직명 ‘다이후’와 상급 여관의 칭호 ‘묘부’로 불리는 궁중 여성."),
        ("검은 담비 가죽옷", "검은 담비 가죽옷: 귀한 모피로 만든 방한복이지만, 작품의 시대에도 매우 고풍스러운 복식으로 묘사된다."),
        ("스에쓰무하나", "스에쓰무하나(末摘花): 줄기 끝에서 따는 잇꽃. 붉은 염료를 얻는 꽃으로, 여인의 붉은 코를 빗댄 통칭이다."),
        ("두툼해진 단지", "단지(檀紙): 닥나무 섬유로 두껍고 희게 만든 고급 일본 종이. 공식 문서와 서간에 널리 썼다."),
    ],
    "07-momijinoga.md": [
        ("청해파", "청해파(青海波): 두 무용수가 짝을 이루어 추는 아악 계통의 춤. 이 장에서 겐지와 도노추조가 함께 춘다."),
        ("주작원", "주작원(朱雀院): 헤이안쿄에 있던 황실의 별궁. 황실 행차와 연회가 열리는 공간이었다."),
        ("겐노나이시노스케", "겐노나이시노스케(源典侍): 내시사의 차관급 여관인 나이시노스케를 지낸 겐씨 여성의 관직형 호칭."),
    ],
    "08-hananoen.md": [
        ("남전", "남전(南殿): 궁궐의 정전인 자진전을 가리키는 별칭. 국가 의식과 큰 연회가 열렸다."),
        ("오보로즈키요", "오보로즈키요(朧月夜): ‘흐릿한 달밤’이라는 뜻. 그 밤의 노래를 계기로 우대신의 딸에게 붙은 통칭이다."),
        ("유화원", "유화원(柳花苑): 버드나무 정원의 정취를 나타내는 궁중 무악의 곡명."),
    ],
    "09-aoi.md": [
        ("가모 축제", "가모 축제(賀茂祭): 교토 가모 신사의 큰 제례. 화려한 행렬을 보려 귀족과 백성이 거리에 모였다."),
        ("재계 의식", "재계(斎戒): 제례에 앞서 부정을 피하고 몸과 마음을 깨끗이 하는 절차."),
        ("생령", "생령(生霊): 살아 있는 사람의 강한 원한이나 집착이 몸을 떠나 다른 사람에게 해를 끼친다고 여긴 영."),
        ("유기리", "유기리(夕霧): 겐지와 아오이노우에 사이에서 태어난 아들. 성장 뒤 작품의 주요 인물이 된다."),
        ("해월 첫 해일", "해월 첫 해일(亥月上亥日): 음력 시월 첫 번째 돼지날. 자손 번성과 무병을 빌며 이노코모치를 먹었다."),
        ("사흘째 밤 예법", "사흘째 밤 예법: 혼인 뒤 사흘째 밤에 떡을 나누며 결합을 공식화하던 헤이안 귀족 사회의 혼례 관습."),
    ],
    "10-sakaki.md": [
        ("재궁", "재궁(斎宮): 이세 신궁에서 천황을 대신해 제사를 모신 미혼의 황녀 또는 여왕."),
        ("노노미야", "노노미야(野宮): 이세로 떠날 재궁이 도성 밖에서 일정 기간 재계하던 임시 궁소."),
        ("사카키", "사카키(賢木·榊): 신도 제례에 쓰는 늘푸른나무. 변치 않는 마음과 신성한 경계를 상징한다."),
        ("중궁", "중궁(中宮): 황후에 준하는 천황의 정실 칭호. 이 작품에서는 후지쓰보가 중궁이 된다."),
        ("오단 수행", "오단 수행(五壇御修法): 다섯 단을 설치하고 다섯 명왕에게 국가와 천황의 안녕을 비는 밀교 의식."),
        ("회지였다", "회지(懐紙): 품속에 넣어 다니며 시를 쓰거나 간단한 메모·용무에 쓰던 종이."),
    ],
    "11-hanachirusato.md": [
        ("레이케이덴 여어", "레이케이덴 여어(麗景殿女御): 선제의 후궁이었던 여인. 자녀가 없어 선제 사후 겐지의 보호를 받는다."),
        ("산노키미", "산노키미(三の君): 레이케이덴 여어의 여동생. 장의 제목인 ‘하나치루사토’로 불리는 겐지의 연인이다."),
        ("왜금", "왜금(和琴): 일본 고유의 여섯 줄 현악기. 궁중 음악과 신사 의식 등에 사용되었다."),
        ("고세치", "고세치(五節): 오절무를 추는 무희를 뜻하는 말에서 온 호칭. 여기서는 규슈로 떠난 겐지의 옛 연인을 가리킨다."),
    ],
}


def without_title(text: str) -> str:
    """Remove the H1 and editorial audit notes from the reader edition."""
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.startswith("# "):
            del lines[index]
            break
    text = "\n".join(lines)
    record_heading = "\n## 번역·대조 기록"
    if record_heading in text:
        text = text.split(record_heading, 1)[0]
        if text.rstrip().endswith("---"):
            text = text.rstrip()[:-3].rstrip()
    return text


def add_footnotes(text: str, filename: str) -> tuple[str, int]:
    """Add short page-footnote spans after selected first occurrences."""
    count = 0
    for needle, note in FOOTNOTES.get(filename, []):
        if needle not in text:
            raise ValueError(f"Footnote anchor not found in {filename}: {needle}")
        replacement = needle + f'<span class="footnote">{html.escape(note)}</span>'
        text = text.replace(needle, replacement, 1)
        count += 1
    return text, count


renderer = markdown.Markdown(extensions=["extra", "sane_lists"], output_format="html5")
chapter_html = []
toc_entries = []
footnote_count = 0

for number, korean, hanja, filename in CHAPTERS:
    anchor = Path(filename).stem
    toc_entries.append((anchor, f"{number} {korean}({hanja})"))
    source = (SOURCE_DIR / filename).read_text(encoding="utf-8")
    source, added = add_footnotes(without_title(source), filename)
    footnote_count += added
    body = renderer.reset().convert(source)
    if filename in LOCAL_IMAGES:
        image_uri = (SOURCE_DIR / LOCAL_IMAGES[filename]).resolve().as_uri()
        body = re.sub(
            r'(<img\s+src=")[^"]+("[^>]*>)',
            rf'\1{image_uri}\2',
            body,
            count=1,
        )
    chapter_html.append(
        f'<section class="chapter" id="{anchor}">'
        f'<header class="chapter-title"><div class="chapter-number">{number}</div>'
        f'<h1>{korean}</h1><div class="chapter-hanja">{hanja}</div></header>'
        f'<div class="chapter-body">{body}</div></section>'
    )

toc = "".join(
    f'<li><a href="#{anchor}">{html.escape(title)}</a></li>'
    for anchor, title in toc_entries
)

css = r"""
@page {
  size: A4;
  margin: 23mm 22mm 23mm 24mm;
  @top-center {
    content: string(chapter);
    font-family: "Noto Serif KR", "AppleMyungjo", serif;
    font-size: 8.5pt;
    color: #777;
  }
  @bottom-center {
    content: counter(page);
    font-family: "Noto Serif KR", "AppleMyungjo", serif;
    font-size: 8.5pt;
    color: #666;
  }
  @footnote {
    border-top: .6px solid #9f948a;
    padding-top: 2.5mm;
    margin-top: 3mm;
  }
}
@page:first {
  @top-center { content: none; }
  @bottom-center { content: none; }
}
@page front {
  @top-center { content: none; }
}

html {
  font-family: "Noto Serif KR", "Nanum Myeongjo", "AppleMyungjo", serif;
  font-size: 10.5pt;
  line-height: 1.78;
  color: #211d19;
}
body { margin: 0; }
p {
  margin: 0 0 .72em;
  text-align: justify;
  overflow-wrap: break-word;
  orphans: 2;
  widows: 2;
}
a { color: inherit; text-decoration: none; }
img { display: block; max-width: 100%; max-height: 160mm; margin: 5mm auto 2mm; object-fit: contain; }
sub { display: block; line-height: 1.45; color: #746b63; }
.footnote {
  float: footnote;
  footnote-policy: block;
  font-size: 8.2pt;
  line-height: 1.45;
  color: #4f4841;
}
.footnote::footnote-call {
  content: counter(footnote);
  font-size: 7pt;
  vertical-align: super;
  line-height: 0;
  color: #8f5f4a;
}
.footnote::footnote-marker {
  content: counter(footnote) ". ";
  color: #8f5f4a;
  font-weight: 700;
}

.title-page {
  page: front;
  height: 245mm;
  box-sizing: border-box;
  padding-top: 55mm;
  text-align: center;
  break-after: page;
}
.title-small { font-size: 12pt; color: #806c5b; letter-spacing: .35em; }
.title-main { margin-top: 9mm; font-size: 35pt; font-weight: 700; letter-spacing: .08em; }
.title-hanja { margin-top: 3mm; font-size: 16pt; color: #65594e; letter-spacing: .28em; }
.title-rule { width: 44mm; border-top: 1.5px solid #8f5f4a; margin: 12mm auto; }
.title-sub { font-size: 14pt; color: #4f4943; }
.title-note { margin-top: 5mm; font-size: 10.5pt; color: #81786f; }
.title-foot { margin-top: 57mm; font-size: 9.5pt; color: #9a9188; }

.toc-page { page: front; break-after: page; padding-top: 12mm; }
.toc-page h1 { text-align: center; font-size: 22pt; margin: 0 0 16mm; }
.toc-page ol { list-style: none; margin: 0; padding: 0 12mm; }
.toc-page li { margin: 5mm 0; font-size: 12pt; }
.toc-page a { display: block; border-bottom: 1px dotted #b9afa6; }
.toc-page a::after { content: target-counter(attr(href), page); float: right; }

.chapter { break-before: page; }
.chapter-title {
  height: 235mm;
  box-sizing: border-box;
  padding-top: 62mm;
  text-align: center;
  break-after: page;
  string-set: chapter "";
}
.chapter-number { color: #8f5f4a; font-size: 13pt; letter-spacing: .35em; }
.chapter-title h1 { margin: 8mm 0 2mm; font-size: 32pt; letter-spacing: .12em; }
.chapter-hanja { color: #776a60; font-size: 16pt; letter-spacing: .3em; }

.chapter-body { string-set: chapter attr(data-title); }
.chapter-body h2 {
  break-before: page;
  break-after: avoid;
  margin: 0 0 8mm;
  padding-bottom: 3mm;
  border-bottom: 1px solid #aa9b8d;
  font-size: 16pt;
  color: #4c4037;
}
.chapter-body ul { margin: .4em 0; padding-left: 1.4em; }
.chapter-body li { margin: .25em 0; }
.chapter-body blockquote {
  margin: 1em 7mm;
  padding: .7em 1em;
  border-left: 2px solid #9b6953;
  background: #f7f3ef;
  color: #473d35;
}
.chapter-body blockquote p { margin: .25em 0; text-align: left; }
.chapter-body hr { border: 0; border-top: 1px solid #c8bdb3; margin: 10mm 38mm; }
"""

# Set the running header on each body without exposing it in the visible text.
for index, ((_, title), fragment) in enumerate(zip(toc_entries, chapter_html)):
    chapter_html[index] = fragment.replace(
        '<div class="chapter-body">',
        f'<div class="chapter-body" data-title="{html.escape(title)}">',
        1,
    )

document = f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><style>{css}</style></head><body>
<section class="title-page">
  <div class="title-small">현대 한국어 완역본</div>
  <div class="title-main">겐지 이야기</div>
  <div class="title-hanja">源氏物語</div>
  <div class="title-rule"></div>
  <div class="title-sub">제1첩–제11첩</div>
  <div class="title-note">기리쓰보에서 하나치루사토까지</div>
  <div class="title-foot">동아시아사 자료 모음</div>
</section>
<section class="toc-page"><h1>차례</h1><ol>{toc}</ol></section>
{''.join(chapter_html)}
</body></html>"""

with tempfile.TemporaryDirectory(prefix="genji-pdf-") as temp_dir:
    html_path = Path(temp_dir) / "genji-1-3.html"
    html_path.write_text(document, encoding="utf-8")
    subprocess.run(
        ["weasyprint", str(html_path), str(OUTPUT)],
        check=True,
        cwd=SOURCE_DIR,
    )

print(f"Wrote {OUTPUT} ({OUTPUT.stat().st_size:,} bytes, {footnote_count} footnotes)")
