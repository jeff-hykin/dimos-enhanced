#!/usr/bin/env -S deno run --allow-all --no-lock
import * as dax from "https://esm.sh/@jsr/david__dax@0.45.0/mod.ts" // see: https://github.com/dsherret/dax
import { FileSystem } from "https://deno.land/x/quickr@0.8.13/main/file_system.js"
import toml from "https://esm.sh/@iarna/toml@2.2.5"
import { Console, green, red, cyan, yellow, magenta } from "https://deno.land/x/quickr@0.8.13/main/console.js"
import { parseArgs, flag, required, initialValue } from "https://esm.sh/gh/jeff-hykin/good-js@1.18.2.0/source/flattened/parse_args.js"
import { toCamelCase } from "https://esm.sh/gh/jeff-hykin/good-js@1.18.2.0/source/flattened/to_camel_case.js"
import { didYouMean } from "https://esm.sh/gh/jeff-hykin/good-js@1.18.2.0/source/flattened/did_you_mean.js"
import Yaml from 'https://esm.sh/yaml@2.4.3'
import { zipLongList as zip } from 'https://esm.sh/gh/jeff-hykin/good-js@1.18.2.0/source/flattened/zip_long_list.js'

import { getChangedFiles, getProjectToml, repoRoot, cliSequence, getAllTestNames } from '../tools.js'

// TODO: pull info (names valid branch types) from pyproject toml

export async function prNaming() {
    // const names = await FileSystem.read(contributorNamesPath)
    // const branchName = await $`git rev-parse --abbrev-ref HEAD`.text()
    // const possibleCorrectNames = await didYouMean({ givenWord: branchName, possibleWords: names, autoThrow: true, suggestionLimit: 1 })
    // if (names.includes(branchName))
    // return cliSequence($=>{
    // })
}