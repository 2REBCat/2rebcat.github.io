---
title: "notify_new_posts 프로젝트"
---

새 게시글이 **main** 브랜치에 추가되면 GitHub Actions가 변경된 markdown 파일 중 어떤 글이 이번에 새로 올라온 글인지 먼저 판별하고, 그 결과를 바탕으로 **upload-post** API를 통해 SNS에 안내 메시지를 올리는 자동화 기록입니다.
