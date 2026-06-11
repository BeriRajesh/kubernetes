import json
import subprocess

warns = open('warnings.log').read().split('\n')


warnings = []
for line in warns:
    if not line:
        continue
    warnings.append(json.loads(line))

for warning in warnings:
    if warning.get('error') == 'IllegalLocationConstraintException':
        bucket_name = warning.get('identifier')
        # print(bucket_name)

        output = subprocess.run(f'grep {bucket_name} csv/*.csv | grep AES', shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)

        lines = output.stdout.split(b'\n')
        for line in lines:
            a=1
            pass
        else:
            if not line:
                continue
            print(bucket_name)
            a=1

    # if warning.get('identifier') == 'RDS':
    #     print('ignore')
    else:
        print(warning.get('region'), warning.get('error'), warning.get('identifier'))

