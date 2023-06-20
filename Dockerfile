# syntax=docker/dockerfile:1
FROM registry.access.redhat.com/ubi8/python-38:latest
USER default
ENV PATH="$HOME/bin:$PATH"
WORKDIR $HOME
COPY --chown=default:root requirements.txt $HOME
COPY --chown=default:root app.py $HOME
RUN pip3 install -r requirements.txt
EXPOSE 5000
HEALTHCHECK CMD curl --fail http://localhost:5000/ || exit 1
CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]
