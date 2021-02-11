import tornado.web
import tornado.ioloop

import asyncio

from baselayer.app.handlers import BaseHandler
from baselayer.app.access import auth_or_token
from baselayer.app.models import DBSession
from shell_service.models import Job


class JobHandler(BaseHandler):
    @auth_or_token
    def get(self, job_id=None):
        """
        ---
        single:
          tags:
            - jobs
          description: Retrieve a job
          parameters:
            - in: path
              name: job_id
              required: true
              schema:
                type: string
          responses:
            200:
               content:
                application/json:
                  schema: SingleJob
            400:
              content:
                application/json:
                  schema: Error
        multiple:
          tags:
            - jobs
          description: Retrieve all jobs
          responses:
            200:
              content:
                application/json:
                  schema: ArrayOfJobs
            400:
              content:
                application/json:
                  schema: Error
        """

        if job_id is not None:
            job = Job.get_if_accessible_by(
                self.current_user, job_id, raise_if_none=True
            )
            return job
        return Job.get_records_accessible_by(self.current_user)

    @auth_or_token
    def post(self):
        """
        ---
        description: Submit a new job to the service
        tags:
          - jobs
        requestBody:
          content:
            application/json:
              schema: JobPostSchema
        responses:
          200:
            content:
              application/json:
                schema: Success
          400:
            content:
              application/json:
                schema: Error

        """
        user_data = self.get_json()
        try:
            job = JobSchema.load(user_data)
        except ValidationError as e:
            return self.error(e.normalized_messages())
        DBSession().add(job)
        self.finalize_transaction()


class ExecutionHandler(BaseHandler):
    @auth_or_token
    async def get(self, job_id):
        """
        ---
        description: Submit a new job to the service
        tags:
          - jobs
        requestBody:
          content:
            application/json:
              schema: JobPostSchema
        responses:
          200:
            content:
              application/json:
                schema: Success
          400:
            content:
              application/json:
                schema: Error

        """
        job = Job.get_if_accessible_by(
            self.current_user, job_id, raise_if_none=True, mode="execute"
        )

        if job.status != "READY":
            return self.error(
                f"Can't execute job: expected READY status, got {job.status}."
            )

        loop = tornado.ioloop.IOLoop.current()
        loop.spawn_callback(self._execute_job, job)

        return self.success()

    async def _execute_job(self, job):
        """Execute a job asynchronously."""
        job.status = "RUNNING"
        self.finalize_transaction()

        # https://docs.python.org/3/library/asyncio-subprocess.html
        # #asyncio.asyncio.subprocess.Process.wait
        proc = await asyncio.create_subprocess_shell(
            job.code, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await proc.communicate()
        job.return_code = proc.returncode
        job.stdout = stdout
        job.stderr = stderr

        if job.return_code == 0:
            job.status = "COMPLETE"
        else:
            job.status = "FAILED"

        self.finalize_transaction()
