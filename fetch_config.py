#!/usr/bin/env python3

import json
import boto3
from pathlib import Path
import sys
import time


class ConfigFetcher:
    def __init__(self, instance_id):
        self.instance_id = instance_id
        # Read region from outputs.json
        outputs = json.loads(Path("outputs.json").read_text())
        region = outputs["VlessProxyStack"]["Region"]
        self.ssm = boto3.client("ssm", region_name=region)

    def fetch_config(self):
        """Fetch Reality configuration"""
        cmd = "sudo bash -c 'bash <(curl -sL https://raw.githubusercontent.com/aleskxyz/reality-ezpz/master/reality-ezpz.sh) --show-user RealityEZPZ'"
        return self.run_command(cmd)

    def run_command(self, command):
        """Run SSM command"""
        response = self.ssm.send_command(
            InstanceIds=[self.instance_id],
            DocumentName="AWS-RunShellScript",
            Parameters={"commands": [command]},
        )
        command_id = response["Command"]["CommandId"]

        while True:
            result = self.ssm.get_command_invocation(
                CommandId=command_id, InstanceId=self.instance_id
            )
            if result["Status"] in ["Success", "Failed", "Cancelled"]:
                if result["Status"] != "Success":
                    raise Exception(result.get("StandardErrorContent", ""))
                return result.get("StandardOutputContent", "")
            time.sleep(1)


def main():
    """Fetch Reality proxy configuration"""
    try:
        # Read instance_id and output from outputs.json
        outputs = json.loads(Path("outputs.json").read_text())
        instance_id = outputs["VlessProxyStack"]["InstanceId"]
        output = "reality-config.txt"

        fetcher = ConfigFetcher(instance_id)
        config = fetcher.fetch_config()
        Path(output).write_text(config)
        print(f"Configuration saved to {output}")

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
