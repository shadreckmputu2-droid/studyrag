# Push to GitHub (Windows cmd)

1. Create an empty repo on github.com named `studyrag` (no README, no .gitignore, no license).
2. In the project folder:

```
git init
git add .
git commit -m "StudyRAG: RAG assistant with citations and evaluation harness"
git branch -M main
git remote add origin https://github.com/<your-username>/studyrag.git
git push -u origin main
```

3. Take two screenshots, save them as `docs\eval-report.png` (open `evals\report.html`) and `docs\web-ui.png`
   (http://localhost:8000 after asking a question), then:

```
git add docs
git commit -m "Add screenshots"
git push
```

4. GitHub Actions runs the tests and the evaluation gate on every push. Add the green badge to the top of the README:
   `![ci](https://github.com/<your-username>/studyrag/actions/workflows/ci.yml/badge.svg)`
5. Optional: deploy the Dockerfile on Render or Railway for a live demo link, and add it to the README.
