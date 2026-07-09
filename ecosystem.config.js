module.exports = {
  apps: [{
    name: "fastapi-bot",
    script: "./venv/bin/uvicorn",
    args: "app:app --host 0.0.0.0 --port 8000",
    cwd: "/home/ngn/llm-docs-pipeline",
    interpreter: "none",
    env: {
      PYTHONUNBUFFERED: "1",
      PATH: "/home/ngn/llm-docs-pipeline/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
    },
    max_memory_restart: "1G",
    log_date_format: "YYYY-MM-DD HH:mm:ss"
  }]
};
