---
title: "upload-post 무료 버전과 Python 구현 메모"
summary: "upload-post 무료 플랜에서 무엇을 확인했고, upload-text API를 Python으로 어떻게 붙일 수 있는지 현재 블로그 자동화 기준으로 정리합니다."
date: 2026-04-29T09:42:01+09:00
lastmod: 2026-04-29T09:42:01+09:00
---

이번 자동화에서는 새 블로그 글이 생겼을 때 SNS에 짧은 소개 문구를 올리기 위해 `upload-post`를 사용했습니다. 처음에는 `X`와 `LinkedIn`에 각각 직접 올리는 방식을 먼저 떠올렸지만, 현재 `X`는 free 티어가 사실상 사라져 게시글 API를 사용할 때마다 비용을 고려해야 했고, `LinkedIn`은 일정 주기마다 키를 다시 갱신해야 해서 운영이 번거로웠습니다.

그래서 두 플랫폼을 각각 따로 붙이는 대신, 여러 채널에 한 번에 올릴 수 있으면서 무료 범위에서도 먼저 실험해 볼 수 있는 통합 API를 찾게 됐고, 그 과정에서 `upload-post`를 선택하게 됐습니다.

## 무료 버전에서 먼저 본 것

공식 문서 첫 화면 기준으로 `upload-post`는 여러 SNS 업로드를 하나의 API로 묶어 주는 서비스이고, 현재 무료로는 매월 10회 업로드를 제공한다고 안내하고 있습니다. 개인 블로그에서 새 글 알림을 자동으로 보내는 용도라면 먼저 무료 범위 안에서 테스트하기에 부담이 적었습니다.

현재 저는 `X`와 `LinkedIn` 계정을 연결해 새 글 알림을 두 곳에 동시에 올리고 있습니다. 이 경우 글 하나를 올릴 때 플랫폼 두 곳으로 각각 업로드가 발생하므로 API 사용량도 2회씩 차감됩니다. 무료 기준이 월 10회라면 실제로는 한 달에 최대 5개 정도의 새 블로그 글을 안정적으로 알릴 수 있다는 계산이 됩니다.

제가 이 프로젝트에서 먼저 확인한 항목은 아래와 같습니다.

1. 텍스트만 올리는 `upload_text` 엔드포인트가 있는지
2. 여러 플랫폼을 한 번에 지정할 수 있는지
3. Python SDK가 있는지
4. 요청 실패 시 어떤 식으로 응답을 받는지

문서 기준으로 `upload_text`는 `X`, `LinkedIn`, `Facebook`, `Threads`, `Reddit`, `Bluesky`, `Google Business Profile`에 대응합니다. 기본 인증은 `Authorization: Apikey ...` 헤더를 사용하고, 필수 파라미터는 `user`, `platform[]`, `title`입니다.

## 이 프로젝트에서 사용한 방식

이 블로그에서는 긴 본문 전체를 SNS에 복사하지 않고, 아래 세 가지만 조합해 안내 메시지를 만들었습니다.

1. 글 제목 `title`
2. 글 요약 `summary`
3. 실제 블로그 주소

즉 SNS 업로드용 원문을 따로 보관하지 않고, Hugo 글의 front matter를 한 번만 관리하도록 맞춘 방식입니다. 새 글을 추가하면 GitHub Actions가 markdown 파일을 찾고, Python 스크립트가 front matter를 읽어 아래 같은 메시지를 만듭니다.

```text
새로운 게시글이 추가되었어요!

게시글 제목

게시글 요약

더 자세한 내용은 Blog에서 확인하세요!
URL: https://2rebcat.github.io/blog/카테고리/슬러그/
```

## Python으로 구현하는 방법

이 리포지토리에서는 공식 Python SDK를 사용했습니다. 워크플로에서 설치하는 패키지는 아래 두 개입니다.

```bash
pip install upload-post pyyaml
```

`pyyaml`은 Hugo front matter를 읽기 위해 필요하고, `upload-post`는 실제 API 호출을 담당합니다.

### 1. 환경 변수 준비

스크립트에서는 아래 환경 변수를 사용합니다.

```text
UPLOAD_POST_API_KEY
UPLOAD_POST_USER
UPLOAD_POST_PLATFORMS
ADDED_FILES
```

이 값들은 로컬 코드에 직접 박아 두는 것이 아니라 GitHub Actions 설정에서 `Secrets`, `Vars`, step 출력값으로 주입하는 방식으로 관리하고 있습니다. 따라서 `UPLOAD_POST_API_KEY`, `UPLOAD_POST_USER`, `UPLOAD_POST_PLATFORMS`를 실제 저장소에서 어떻게 넣는지는 이 글에서 코드 기준으로만 가볍게 보고, 자세한 설정 순서와 화면 기준 설명은 뒤의 GitHub Actions 관련 글에서 따로 정리하려고 합니다.

특히 `UPLOAD_POST_API_KEY`처럼 외부 API 인증에 직접 쓰이는 값은 저장소 본문이나 스크립트 파일에 그대로 적어 두면 노출 위험이 커집니다. GitHub Actions의 `Secrets`를 사용하면 중요한 인증 정보가 코드와 분리되고, 작업 로그나 공개 저장소 이력에서 실수로 드러날 가능성도 줄일 수 있습니다. 이 프로젝트에서도 민감한 값은 `Secrets`로, 상대적으로 운영 옵션에 가까운 값은 `Vars`로 나눠 두어 중요한 정보가 불필요하게 노출되지 않도록 관리하고 있습니다.

각 역할은 다음과 같습니다.

1. `UPLOAD_POST_API_KEY`: upload-post API 키
2. `UPLOAD_POST_USER`: upload-post에서 사용하는 사용자 식별자
3. `UPLOAD_POST_PLATFORMS`: 쉼표로 구분한 플랫폼 목록 예시 `x,threads,bluesky`
4. `ADDED_FILES`: 이번 push에서 새로 추가된 markdown 파일 목록

### 2. SDK로 텍스트 업로드하기

문서의 `upload-text` 설명을 보면 필수 필드는 `user`, `platform[]`, `title`입니다. Python SDK에서는 이를 아래처럼 보낼 수 있습니다.

```python
import os
from upload_post import UploadPostClient

api_key = os.environ["UPLOAD_POST_API_KEY"].strip()
user = os.environ["UPLOAD_POST_USER"].strip()
platforms = ["x", "threads"]

message = """새 글을 발행했습니다.\n\n정적 사이트 운영 전에 확인할 최소 체크리스트\n\n배포 전에 확인할 항목을 짧게 정리했습니다.\n\nURL: https://2rebcat.github.io/blog/security-ops/static-site-checklist/"""

client = UploadPostClient(api_key)
response = client.upload_text(
	title=message,
	user=user,
	platforms=platforms,
)

print(response)
```

이 프로젝트도 같은 흐름으로 동작합니다. 다만 문자열을 하드코딩하지 않고, markdown front matter에서 제목과 요약을 읽어 메시지를 조합합니다.

### 3. 실제 리포지토리에서 쓰는 예시

현재 리포지토리의 `.github/scripts/notify_new_posts.py`는 다음 순서로 동작합니다.

1. `ADDED_FILES`에서 이번에 추가된 markdown 파일 목록을 읽음
2. `_index.md`와 블로그 본문이 아닌 파일을 제외함
3. 파일의 front matter에서 `title`, `summary`를 읽음
4. Hugo 경로를 실제 블로그 URL로 변환함
5. `client.upload_text(...)`로 플랫폼별 업로드를 요청함

핵심 부분만 줄이면 아래와 비슷합니다.

```python
from pathlib import Path
import os
import yaml
from upload_post import UploadPostClient

SITE_BASE = "https://2rebcat.github.io"


def parse_front_matter(path: Path) -> dict:
	text = path.read_text(encoding="utf-8")
	_, fm, _ = text.split("---", 2)
	return yaml.safe_load(fm) or {}


def build_post_url(path: Path) -> str:
	rel = path.relative_to("content/blog")
	topic = rel.parts[0]
	slug = rel.stem
	return f"{SITE_BASE}/blog/{topic}/{slug}/"


client = UploadPostClient(os.environ["UPLOAD_POST_API_KEY"])
platforms = [
	item.strip()
	for item in os.environ.get("UPLOAD_POST_PLATFORMS", "x").split(",")
	if item.strip()
]

path = Path("content/blog/security-ops/static-site-checklist.md")
fm = parse_front_matter(path)
message = (
	"새로운 게시글이 추가되었어요!\n\n"
	f"{fm['title']}\n\n"
	f"{fm['summary']}\n\n"
	f"URL: {build_post_url(path)}"
)

result = client.upload_text(
	title=message,
	user=os.environ["UPLOAD_POST_USER"],
	platforms=platforms,
)

print(result)
```

## `upload-text` 문서를 보며 같이 기억할 점

공식 문서 기준으로 같이 확인해 둘 만한 부분도 있습니다.

1. `title`은 사실상 본문 역할을 합니다.
2. `description`은 Reddit에서만 확장 본문으로 사용됩니다.
3. `link_url`을 함께 보내면 링크 미리보기를 붙일 수 있는 플랫폼이 있습니다.
4. 요청이 오래 걸리면 동기 요청이어도 비동기 처리로 전환될 수 있습니다.
5. `Idempotency-Key`나 `request_id`를 사용하면 재시도 중복 업로드를 줄일 수 있습니다.

지금 스크립트는 가장 단순한 텍스트 업로드만 사용하지만, 이후에는 `link_url`을 같이 보내서 블로그 링크 미리보기를 띄우는 방식으로 확장할 수 있습니다.

## 정리

무료 범위에서 테스트를 시작하고, 글의 `title`과 `summary`만 잘 관리해도 블로그 새 글 알림 자동화는 충분히 만들 수 있었습니다. 핵심은 SNS 전용 데이터를 별도로 또 만들지 않고, Hugo front matter를 재사용하도록 흐름을 단순하게 유지하는 것입니다. 전체 코드는 `https://github.com/2REBCat/2rebcat.github.io/blob/main/.github/scripts/notify_new_posts.py`에서 볼 수 있고, 링크가 아니어도 저장소 루트 기준 `.github/scripts/notify_new_posts.py` 경로로 직접 열어 같은 파일에 접근할 수 있습니다.

