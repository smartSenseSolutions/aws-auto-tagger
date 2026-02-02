from src.services import SERVICE_CONFIGS
import yaml
import re


def test_validate_sls_policy():
    clients = list(SERVICE_CONFIGS.keys())
    with open("serverless.yml", "r") as file:
        yaml_file = yaml.safe_load(file)

    # print(clients)
    sls_role = yaml_file["provider"]["iam"]["role"]
    actions = [
        action for statement in sls_role["statements"] for action in statement["Action"]
    ]

    missing_services = []
    for service in clients:
        for action in actions:
            if re.search(service, action):
                break
        else:
            missing_services.append(service)

    if missing_services:
        assert False, (
            f"Error: IAM Actions {missing_services} is not present in the serverless.yml file"
        )
    else:
        print("All services are present in the serverless.yml file")
        assert True
