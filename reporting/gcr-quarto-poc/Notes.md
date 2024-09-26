# Notes

- can see images with `docker images` and remove with `docker rmi <id>` to remove, especially needed for Cloud Editor as docker images can be larger than 1GB per image build.
- `RUN pip install --upgrade pip ipython ipykernel` is needed for the build, isolating outside of requirements to be explicit on upgrade after the installs just in case
- `CMD ["gunicorn", "-b", "0.0.0.0:8080", "report_render:app"]` needs to enter the flask app.  LLMs might say main,but this will yield an invalid arugments error.
- Quarto needs a cell tagged parameters
- Pass in parameters now with `-P` 
- The flow used explicitly outputs the file name, and that is passed onto the next task.
