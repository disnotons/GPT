# ChatGPT 공개 아카이브

ChatGPT 공식 데이터 내보내기를 화면 표시 대화 기준으로 변환한 공개 아카이브입니다.

현재 준비된 공개본에는 자동 공개 필터를 통과한 **1,358개 대화**가 포함되어 있습니다.

## 게시 방식

이 저장소는 `GPT_PUBLIC_ARCHIVE_READY.zip`을 받아 자동으로 GitHub Pages 사이트를 배포하도록 구성합니다.

압축 파일 내부 구조는 다음과 같습니다.

- `publish_site/index.md` — 전체 색인
- `publish_site/categories.md` — 분야별 보기
- `publish_site/search.html` — 제목 검색
- `publish_site/privacy.md` — 공개 필터 기준
- `publish_site/conversations/` — 개별 대화 Markdown
- `publish_site/_config.yml` — Jekyll 설정

GitHub Actions 워크플로는 ZIP을 풀어 `publish_site/`를 Pages artifact로 업로드한 뒤 배포합니다.
