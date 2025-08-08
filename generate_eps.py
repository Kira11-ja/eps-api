name: update_eps

on:
  workflow_dispatch: {}            # 手動跑
  schedule:
    - cron: "0 2 * * *"            # 每天 02:00 自動跑（不需要就刪掉這段）

permissions:
  contents: write                  # 允許寫入 repo（搭配 token 更保險）

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repo
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
          # 使用你在 Secrets 建的 PAT（名稱 GH_PAT）
          token: ${{ secrets.GH_PAT }}

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run scraper
        run: |
          python generate_eps.py

      - name: Show outputs (debug)
        run: |
          echo "PWD=$(pwd)"
          ls -la
          echo "---- JSON files ----"
          ls -la *.json || true
          echo "---- First lines of eps_cache.json ----"
          test -f eps_cache.json && head -n 20 eps_cache.json || echo "eps_cache.json not found"

      - name: Ensure eps_cache.json exists
        run: |
          if [ ! -f eps_cache.json ]; then
            echo "❌ eps_cache.json not found. Stop."
            exit 1
          fi

      - name: Commit and push if changed
        run: |
          git config user.name  "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"

          git add eps_cache.json

          # 沒有變更就不要 commit / push
          if git diff --cached --quiet; then
            echo "No changes to commit."
            exit 0
          fi

          git commit -m "✅ Update EPS cache [skip ci]"
          git push
