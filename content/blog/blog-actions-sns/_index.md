---
title: "notify_new_posts 프로젝트"
---

새 게시글이 `main` 브랜치에 추가되면 GitHub Actions가 변경된 markdown 파일 중 어떤 글이 이번에 새로 올라온 글인지 먼저 판별하고, 그 결과를 바탕으로 `upload-post` API를 통해 SNS에 안내 메시지를 올리는 자동화 기록입니다. Hugo 글의 front matter에서 제목과 요약을 읽어 공지 문구를 만들고, `Secrets`와 `Vars`를 분리해 운영하는 과정도 함께 정리합니다.
