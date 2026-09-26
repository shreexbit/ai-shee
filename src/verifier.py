import subprocess


class Verifier:

    def run_tests(self, repository_path):

        evaluation_tests = "eval_tests"

        try:

            result = subprocess.run(
                [
                    "python",
                    "-m",
                    "pytest",
                    evaluation_tests
                ],
                capture_output=True,
                text=True
            )

            return {
                "success": result.returncode == 0,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }

        except Exception as error:

            return {
                "success": False,
                "return_code": -1,
                "stdout": "",
                "stderr": str(error)
            }