---
title: "GitHub Actions로 새 글 알림 자동화하기"
date: 2026-05-06T08:59:16+09:00
lastmod: 2026-05-06T08:59:16+09:00
summary: "새 블로그 글이 추가되면 GitHub Actions가 이를 감지하고 upload-post API로 SNS 공지를 보내도록 구성한 흐름을 정리합니다."
---

블로그 운영에서는 글을 발행한 뒤 링크를 따로 정리해서 SNS에 올리는 작업이 자주 남습니다. 이번에는 그 반복 작업을 줄이기 위해 GitHub Actions로 새 글 추가를 감지하고, `upload-post` API를 호출하는 흐름을 붙였습니다.

## 전체 흐름

현재 워크플로는 아래 순서로 동작합니다.

1. `main` 브랜치에 push가 발생함
2. 변경 경로가 `content/blog/**/*.md`와 맞는지 확인함
3. 이번 push에서 새로 추가된 markdown 파일만 골라냄
4. Python 스크립트가 각 파일의 `title`, `summary`를 읽음
5. SNS에 올릴 문구를 만들고 `upload-post`로 전송함

즉 수정된 글 전체를 다시 알리는 방식이 아니라, `git diff --diff-filter=A`를 사용해 이번에 추가된 새 파일만 공지합니다. 폴더 소개용 `_index.md`는 스크립트에서 제외합니다.

## `.github`에 무엇을 두었는가

이 프로젝트에서 실제로 사용하는 위치는 아래 두 군데입니다.

```text
.github/
	workflows/
		notify-new-posts.yml
	scripts/
		notify_new_posts.py
```

각 역할은 명확하게 나눴습니다.

1. `workflows/notify-new-posts.yml`: 언제 실행할지, 어떤 런타임을 쓸지, 어떤 환경 변수를 넘길지 담당
2. `scripts/notify_new_posts.py`: 파일 목록을 읽고 front matter를 파싱해서 API를 호출하는 실제 로직 담당

이렇게 나누면 워크플로 파일은 배선만 맡고, 로직 변경은 Python 스크립트에서 처리할 수 있어서 유지보수가 편합니다.

## 워크플로 파일에서 하는 일

현재 YAML의 핵심은 아래와 같습니다.

```yaml
name: Notify new blog posts

on:
	push:
		branches:
			- main
		paths:
			- 'content/blog/**/*.md'

jobs:
	notify:
		runs-on: ubuntu-latest
		steps:
			- uses: actions/checkout@v4
				with:
					fetch-depth: 0

			- name: Determine added blog files
				id: diff
				run: |
					ADDED=$(git diff --name-only --diff-filter=A "$BEFORE" "$AFTER" -- 'content/blog/**/*.md' || true)

			- uses: actions/setup-python@v5
				if: steps.diff.outputs.added != ''
				with:
					python-version: '3.12'

			- name: Install dependencies
				if: steps.diff.outputs.added != ''
				run: pip install upload-post pyyaml

			- name: Notify upload-post.com
				if: steps.diff.outputs.added != ''
				env:
					UPLOAD_POST_API_KEY: ${{ secrets.UPLOAD_POST_API_KEY }}
					UPLOAD_POST_USER: ${{ secrets.UPLOAD_POST_USER }}
					UPLOAD_POST_PLATFORMS: ${{ vars.UPLOAD_POST_PLATFORMS }}
					ADDED_FILES: ${{ steps.diff.outputs.added }}
				run: python .github/scripts/notify_new_posts.py
```

여기서 중요하게 본 부분은 세 가지였습니다.

1. `paths`로 블로그 markdown 변경에만 반응하게 제한한 점
2. 새 파일이 없으면 Python 설치와 API 호출을 건너뛰게 한 점
3. 민감 정보는 `Secrets`, 운영 옵션은 `Vars`로 나눈 점

## Secrets는 무엇을 넣었는가

GitHub Actions에서 `Secrets`는 로그에 노출되면 안 되는 값을 보관할 때 씁니다. 이 프로젝트에서는 아래 두 개를 넣었습니다.

```text
UPLOAD_POST_API_KEY
UPLOAD_POST_USER
```

실제 사용 기준으로 보면 다음처럼 나뉩니다.

1. `UPLOAD_POST_API_KEY`: 반드시 비공개여야 하는 인증 키
2. `UPLOAD_POST_USER`: API 요청에 함께 보내는 사용자 식별값

`UPLOAD_POST_USER`는 성격상 공개 가능 여부를 팀 정책에 따라 다르게 볼 수 있지만, 지금 구성에서는 함께 `Secrets`로 넣어 관리했습니다. 운영 기준이 아직 작고 단순하다면 이 편이 덜 헷갈립니다.

### Secrets 설정 방법

GitHub 저장소에서 아래 순서로 추가할 수 있습니다.

1. 저장소 페이지로 이동
2. `Settings`
3. `Secrets and variables`
4. `Actions`
5. `New repository secret`

이름은 워크플로에서 쓰는 값과 정확히 같아야 합니다.

```text
UPLOAD_POST_API_KEY
UPLOAD_POST_USER
```

## Vars는 무엇을 넣었는가

`Vars`는 민감하지 않지만 배포 환경에서 바뀔 수 있는 값을 둘 때 편합니다. 이 프로젝트에서는 플랫폼 목록을 `Vars`로 분리했습니다.

```text
UPLOAD_POST_PLATFORMS
```

예를 들면 아래처럼 설정할 수 있습니다.

```text
x
x,threads
x,threads,bluesky
```

Python 스크립트에서는 이 문자열을 쉼표로 나누어 리스트로 바꿉니다. 즉 플랫폼을 늘리거나 줄일 때 YAML이나 Python 코드를 수정하지 않고도 저장소 설정에서 조정할 수 있습니다.

### Vars 설정 방법

경로는 `Secrets`와 거의 같습니다.

1. 저장소 페이지로 이동
2. `Settings`
3. `Secrets and variables`
4. `Actions`
5. `Variables` 탭 선택
6. `New repository variable`

이름은 `UPLOAD_POST_PLATFORMS`, 값은 예를 들어 `x,threads`처럼 넣으면 됩니다.

## Python 스크립트에서 하는 일

워크플로가 넘긴 `ADDED_FILES`를 받아서 실제로 처리하는 쪽은 `.github/scripts/notify_new_posts.py`입니다. 이 스크립트는 다음 기준으로 동작합니다.

1. `content/blog/` 아래 파일만 처리함
2. `_index.md`는 제외함
3. 파일이 실제로 존재하는지 확인함
4. front matter에 `title`, `summary`가 둘 다 있을 때만 업로드함

이 기준을 둔 이유는 폴더 소개 페이지나 초안 상태 문서를 잘못 알리는 일을 줄이기 위해서입니다. 특히 `summary`를 필수로 본 덕분에 SNS에 올라가는 문구 품질을 front matter 단계에서 같이 관리할 수 있었습니다.

## 운영하면서 느낀 점

GitHub Actions로 자동화할 때 중요한 것은 복잡한 기능을 한 번에 다 넣는 것보다, 실패했을 때 어디를 보면 되는지 흐름을 분리해 두는 것입니다. 이 구성에서는 다음이 특히 도움이 됐습니다.

1. 트리거는 YAML에서 관리
2. 메시지 생성은 Python에서 관리
3. 인증 정보는 `Secrets`
4. 플랫폼 선택은 `Vars`

이렇게 나누면 어느 단계에서 바꿔야 할지 바로 보입니다. 예를 들어 플랫폼을 늘리는 것은 `Vars` 수정으로 끝나고, 문구 형식을 바꾸는 것은 Python 스크립트만 손보면 됩니다.

## 정리

새 글 알림 자동화는 기능 자체보다 경계 정리가 더 중요했습니다. GitHub Actions는 실행 조건과 환경 전달만 맡기고, 실제 공지 생성은 Python으로 분리해 두니 수정 포인트가 분명해졌습니다. 블로그를 계속 운영할수록 이런 작은 반복 작업을 저장소 안에서 닫아 두는 방식이 훨씬 편합니다.
