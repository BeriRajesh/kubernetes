cat ${1:-nohup.out} | grep -i "Encrypting bucket_name" | uniq
