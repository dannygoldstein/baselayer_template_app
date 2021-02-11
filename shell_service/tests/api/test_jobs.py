from shell_service.tests import api
import uuid
import time


def test_token_admin_user_can_submit_and_retrieve_job(
    super_admin_user, super_admin_user_token
):

    job_name = f"hello_world_{uuid.uuid4().hex}"
    job_script = "echo 'hello world'"

    status, data = api(
        "POST",
        "jobs",
        data={"id": job_name, "code": job_script},
        token=super_admin_user_token,
    )

    assert status == 200
    assert data["status"] == "success"

    status, data = api("GET", f"jobs/{job_name}", token=super_admin_user_token)

    assert status == 200
    assert data["status"] == "success"
    assert data["data"]["submitter_id"] == super_admin_user.id
    assert data["data"]["status"] == "READY"


def test_token_user_can_submit_and_retrieve_job(user, user_token):

    job_name = f"hello_world_{uuid.uuid4().hex}"
    job_script = "echo 'hello world'"

    status, data = api(
        "POST", "jobs", data={"id": job_name, "code": job_script}, token=user_token
    )

    assert status == 200
    assert data["status"] == "success"

    status, data = api("GET", f"jobs/{job_name}", token=user_token)

    assert status == 200
    assert data["status"] == "success"
    assert data["data"]["submitter_id"] == user.id
    assert data["data"]["status"] == "READY"


def test_token_admin_user_can_submit_and_execute_job(
    super_admin_user, super_admin_user_token
):

    job_name = f"hello_world_{uuid.uuid4().hex}"
    job_script = "echo 'hello world'"

    status, data = api(
        "POST",
        "jobs",
        data={"id": job_name, "code": job_script},
        token=super_admin_user_token,
    )

    assert status == 200
    assert data["status"] == "success"

    status, data = api("GET", f"execute/{job_name}", token=super_admin_user_token)

    assert status == 200
    assert data["status"] == "success"

    start = time.time()
    while True:
        # wait for the job to finish
        current = time.time()
        if current - start >= 10:
            raise TimeoutError("Server response timed out.")

        status, data = api("GET", f"jobs/{job_name}", token=super_admin_user_token)

        assert status == 200
        assert data["status"] == "success"
        assert data["data"]["submitter_id"] == super_admin_user.id
        if data["data"]["status"] not in ["READY", "RUNNING"]:
            break

    assert data["data"]["status"] == "COMPLETE"
    assert "hello world" in data["data"]["stdout"]
    assert data["data"]["return_code"] == 0


def test_token_user_submit_and_execute_50_jobs_at_once_no_blocking(user, user_token):

    job_names = [f"long_hello_world_{uuid.uuid4().hex}" for _ in range(50)]
    job_script = "sleep 2; echo 'hello world'"

    for job_name in job_names:
        status, data = api(
            "POST", "jobs", data={"id": job_name, "code": job_script}, token=user_token
        )

        assert status == 200
        assert data["status"] == "success"

        status, data = api("GET", f"execute/{job_name}", token=user_token)

        assert status == 200
        assert data["status"] == "success"

    start = time.time()
    while True:
        # wait for the job to finish
        current = time.time()
        if current - start >= 10:
            raise TimeoutError("Server response timed out.")
        status, data = api("GET", f"jobs", token=user_token)

        assert status == 200
        assert data["status"] == "success"

        jobs = {job["id"]: job for job in data["data"]}
        if all(
            [jobs[name]["status"] not in ["READY", "RUNNING"] for name in job_names]
        ):
            break

    assert all([jobs[name]["status"] == "COMPLETE" for name in job_names])
    assert all(["hello world" in jobs[name]["stdout"] for name in job_names])
    assert all([jobs[name]["return_code"] == 0 for name in job_names])


def test_token_user_cannot_rerun_already_run_job(user, user_token):

    job_name = f"hello_world_{uuid.uuid4().hex}"
    job_script = "echo 'hello world'"

    status, data = api(
        "POST", "jobs", data={"id": job_name, "code": job_script}, token=user_token
    )

    assert status == 200
    assert data["status"] == "success"

    status, data = api("GET", f"execute/{job_name}", token=user_token)

    assert status == 200
    assert data["status"] == "success"

    start = time.time()
    while True:
        # wait for the job to finish
        current = time.time()
        if current - start >= 10:
            raise TimeoutError("Server response timed out.")

        status, data = api("GET", f"jobs/{job_name}", token=user_token)

        assert status == 200
        assert data["status"] == "success"
        assert data["data"]["submitter_id"] == user.id
        if data["data"]["status"] not in ["READY", "RUNNING"]:
            break

    assert data["data"]["status"] == "COMPLETE"
    assert "hello world" in data["data"]["stdout"]
    assert data["data"]["return_code"] == 0

    status, data = api("GET", f"execute/{job_name}", token=user_token)

    # already ran this job - can't run it again
    assert status == 400
    assert data["status"] == "error"


def test_token_user_cannot_run_other_users_job(
    user, user_token, super_admin_user_token
):

    job_name = f"hello_world_{uuid.uuid4().hex}"
    job_script = "echo 'hello world'"

    status, data = api(
        "POST",
        "jobs",
        data={"id": job_name, "code": job_script},
        token=super_admin_user_token,
    )

    assert status == 200
    assert data["status"] == "success"

    status, data = api("GET", f"execute/{job_name}", token=user_token)

    assert status == 400
    assert data["status"] == "error"


def test_invalid_job_names_are_rejected(user, user_token, super_admin_user_token):

    # illegal space
    job_name = f"hello world_{uuid.uuid4().hex}"
    job_script = "echo 'hello world'"

    status, data = api(
        "POST",
        "jobs",
        data={"id": job_name, "code": job_script},
        token=super_admin_user_token,
    )

    assert status == 400
    assert data["status"] == "error"

    job_name = f""
    job_script = "echo 'hello world'"

    status, data = api(
        "POST",
        "jobs",
        data={"id": job_name, "code": job_script},
        token=super_admin_user_token,
    )

    assert status == 400
    assert data["status"] == "error"


def test_token_admin_user_can_submit_and_execute_job_expected_to_fail(
    super_admin_user, super_admin_user_token
):

    job_name = f"hello_world_{uuid.uuid4().hex}"
    job_script = "ecfdho 'hello world'"

    status, data = api(
        "POST",
        "jobs",
        data={"id": job_name, "code": job_script},
        token=super_admin_user_token,
    )

    assert status == 200
    assert data["status"] == "success"

    status, data = api("GET", f"execute/{job_name}", token=super_admin_user_token)

    assert status == 200
    assert data["status"] == "success"

    start = time.time()
    while True:
        # wait for the job to finish
        current = time.time()
        if current - start >= 10:
            raise TimeoutError("Server response timed out.")

        status, data = api("GET", f"jobs/{job_name}", token=super_admin_user_token)

        assert status == 200
        assert data["status"] == "success"
        assert data["data"]["submitter_id"] == super_admin_user.id
        if data["data"]["status"] not in ["READY", "RUNNING"]:
            break

    assert data["data"]["status"] == "FAILED"
    assert data["data"]["return_code"] != 0
