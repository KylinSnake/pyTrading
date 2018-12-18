#!/usr/bin/bash

ls Test | grep "\.py" | sed 's/\.py//g' | xargs -I {} sh -c ' echo "Run Test {}:" && python3 -m Test.{} && echo Done'
