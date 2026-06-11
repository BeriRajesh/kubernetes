#!/bin/bash

echo "This script is deprecated, please use `select_hosts.py`. Follow instruction in the readme.md in this folder"
exit 1

HOSTS='!platform_windows'
COMMAND=""
SHELL=""
INVENTORY="hosts-us/hosts"
REFRESH=0

while getopts ":a:c:e:i:l:L:p:r:s:S:" opt; do
  case $opt in
    a)
      echo "application was triggered, Parameter: $OPTARG" >&2
      HOSTS="$HOSTS:&tag_Application_$OPTARG"
      ;;
    e)
      echo "environment was triggered, Parameter: $OPTARG" >&2
      HOSTS="$HOSTS:&tag_Environment_$OPTARG"
      ;;
    l)
      echo "layer was triggered, Parameter: $OPTARG" >&2
      HOSTS="$HOSTS:&tag_Layer_$OPTARG"
      ;;
    L)
      echo "layer was triggered, Parameter: $OPTARG" >&2
      if [ -z "$COMMAND" ]
      then
        COMMAND="--list-hosts"
      fi
      ;;
    p)
      echo "platform was triggered, Parameter: $OPTARG" >&2
      HOSTS="$HOSTS:&platform_$OPTARG"
      ;;
    s)
      echo "service-group was triggered, Parameter: $OPTARG" >&2
      HOSTS="$HOSTS:&tag_ServiceGroup_$OPTARG"
      ;;
    S)
      echo "shell was triggered, Parameter: $OPTARG" >&2
      SHELL="-m shell -a '$OPTARG'"
      ;;
    c)
      echo "command was triggered, Parameter: $OPTARG" >&2
      COMMAND=$OPTARG
      ;;
    i)
      echo "inventory was triggered, Parameter: $OPTARG" >&2

      if [ "$OPTARG" = "us" ]
      then
        INVENTORY="hosts-us/hosts"
      elif [ "$OPTARG" = "eu" ]
      then
        INVENTORY="hosts-eu/hosts"
      else
        INVENTORY=$OPTARG
      fi
      ;;
    r)
      echo "REFRESHING INVENTORY"
      REFRESH=1
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      exit 1
      ;;
    :)
      echo "Option -$OPTARG requires an argument." >&2
      exit 1
      ;;
  esac
done
shift $((OPTIND -1))

if [ $REFRESH -eq 1 ]
then
    $INVENTORY --refresh > /dev/null
fi

if [ -z "$COMMAND" ]
then
    COMMAND="--list-hosts"
fi



echo $1

ANSIBLE_COMMAND="ansible $HOSTS -i $INVENTORY $COMMAND $SHELL"



$ANSIBLE_COMMAND

echo "command was: $ANSIBLE_COMMAND"


