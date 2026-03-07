#!/usr/bin/env -S deno run --allow-all --no-lock
import * as dax from "https://esm.sh/@jsr/david__dax@0.45.0/mod.ts" // see: https://github.com/dsherret/dax
import { $ } from "https://esm.sh/@jsr/david__dax@0.45.0/mod.ts" // see: https://github.com/dsherret/dax
import { env, aliases, $stdout, $stderr, initHelpers, iterateOver } from "https://esm.sh/gh/jeff-hykin/bash2deno@0.1.0.2/helpers.js"
import { FileSystem, glob } from "https://deno.land/x/quickr@0.8.13/main/file_system.js"
import toml from "https://esm.sh/@iarna/toml@2.2.5"
import { zipLongList as zip } from 'https://esm.sh/gh/jeff-hykin/good-js@1.18.2.0/source/flattened/zip_long_list.js'

export const testCachePath = `${FileSystem.thisFolder}/test_cache.json`
export const checkPrCachePath = `${FileSystem.thisFolder}/check_pr_cache.json`
export const repoRoot = FileSystem.normalizePath(`${FileSystem.thisFolder}/..`)
export const write = (text)=>Deno.stdout.writeSync(text instanceof Uint8Array ? text : new TextEncoder().encode(text))


// Helpers
export const hasCommand = async (cmd) => {
    try {
        await $$`command -v ${cmd}`.quiet()
        return true
    } catch {
        return false
    }
}

export const printOutput = (result) => {
    const chunks = []
    if (result?.stdout?.trim()) {
        const text = result.stdout.trimEnd()
        chunks.push(text)
        console.log(text)
    }
    if (result?.stderr?.trim()) {
        const text = result.stderr.trimEnd()
        chunks.push(text)
        console.log(text)
    }
    return chunks.join("\n")
}

export async function getChangedFiles() {
    // changed files
    var committedFiles = (await $`git diff --name-only dev...HEAD -- '*.py'`.text("combined")).split(/\n+/g).filter(each=>each)
    var uncomittedFiles = (await $`git status --porcelain=v1 -z`.text("combined")).split(/\0+/g).filter(each=>each).map(each=>each.slice(3))
    var trackedFiles = new Set((await $`git ls-files -z`.text("combined")).split(/\0+/g).filter(each=>each))
    committedFiles = committedFiles.filter(each=>trackedFiles.has(each))
    uncomittedFiles = uncomittedFiles.filter(each=>trackedFiles.has(each))
    var files = [...new Set(committedFiles.concat(uncomittedFiles))]

    // if a file is edited, find all tests in the directory of that file (do for each edited file)
    var dirs = new Set()
    var testFiles = new Set()
    for (let each of files) {
        dirs.add(FileSystem.dirname(each))
    }
    for (let each of dirs) {
        const absoluteDir = `${repoRoot}/${each}`
        let allFilesInDir = await FileSystem.listFileItemsIn(absoluteDir)
        for (let each of allFilesInDir) {
            each.name.startsWith("test_") && testFiles.add(each.path)
        }
    }

    // the files that don't exist are the ones that are deleted on this branch but exist on dev
    var filesExistanceStatus = (await Promise.all(files.map(file => FileSystem.exists(file))))
    var filesThatExist = zip(files, filesExistanceStatus).filter(([file,existance])=>existance).map(([file,existance])=>file)
    testFiles = [...testFiles] // convert to array
    return { files, filesThatExist, testFiles, committedFiles, uncomittedFiles }
}

export async function getProjectToml() {
    var pyprojectToml = await Deno.readTextFile(`${FileSystem.thisFolder}/../pyproject.toml`)
    var parsedToml = toml.parse(pyprojectToml)
    return parsedToml
}

export function buildCollectorScript() {
    return `import contextlib
import io
import json
import pytest

class Collector:
    def __init__(self):
        self.items = []

    def pytest_collection_finish(self, session):
        for item in session.items:
            markers = sorted({m.name for m in item.iter_markers()})
            self.items.append({\"nodeid\": item.nodeid, \"markers\": markers})

collector = Collector()

buf = io.StringIO()
with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
    ret = pytest.main([\"--collect-only\", \"-q\", \"--disable-warnings\", \"--continue-on-collection-errors\", \"-p\", \"no:warnings\", \"-o\", \"addopts=\"], plugins=[collector])

print(json.dumps({\"items\": collector.items, \"retcode\": ret, \"output\": buf.getvalue()}))
`
}

export async function collectTests(pythonCmd = null) {
    const scriptPath = await Deno.makeTempFile({ suffix: ".py" })
    try {
        await Deno.writeTextFile(scriptPath, buildCollectorScript())
        // Use provided python command or default to venv python
        const venvPython = `${repoRoot}/.venv/bin/python`
        const python = pythonCmd || ((await FileSystem.exists(venvPython)) ? venvPython : "python")
        const collectRaw = await dax.$`${python} ${scriptPath}`.text()
        return JSON.parse(collectRaw)
    } finally {
        await Deno.remove(scriptPath).catch(() => {})
    }
}

// Generic cache management
export async function loadCache(path, defaultValue = {}) {
    try {
        const raw = await Deno.readTextFile(path)
        const parsed = JSON.parse(raw)
        if (parsed && typeof parsed === "object") {
            return parsed
        }
    } catch {
        // ignore missing or invalid cache
    }
    return defaultValue
}

export async function saveCache(path, cache) {
    const json = JSON.stringify(cache, null, 2)
    await Deno.writeTextFile(path, json + "\n")
}

// Backwards compatibility wrappers
async function loadTestCache(path) {
    return await loadCache(path, { tests: {} })
}

async function saveTestCache(path, cache) {
    return await saveCache(path, cache)
}

export async function getAllTestNames(useCache = false) {
    const cache = await loadTestCache(testCachePath)
    if (useCache && Array.isArray(cache.test_list) && cache.test_list.length > 0) {
        return { items: cache.test_list, cache, retcode: 0, output: "", usedCache: true }
    }

    const collection = await collectTests()
    const items = collection.items || []
    cache.test_list = items
    await saveTestCache(testCachePath, cache)
    return {
        items,
        cache,
        retcode: collection.retcode ?? 0,
        output: collection.output || "",
        usedCache: false,
    }
}

export function normalizePipeOutput(value) {
    if (value == null) return ""
    if (typeof value === "string") return value
    if (value instanceof Uint8Array) {
        return new TextDecoder().decode(value)
    }
    return String(value)
}

function writeBytes(target, text) {
    if (!text) return
    const bytes = new TextEncoder().encode(text)
    target.writeSync(bytes)
}

export async function cliSequence(run) {
    const stdoutChunks = []
    const stderrChunks = []

    const wrapCommand = (cmd) => {
        return new Proxy(cmd, {
            get(target, prop) {
                if (prop === "then") {
                    return (onFulfilled, onRejected) => target.then(
                        (result) => {
                            const stdoutText = normalizePipeOutput(result?.stdout)
                            const stderrText = normalizePipeOutput(result?.stderr)
                            if (stdoutText) stdoutChunks.push(stdoutText)
                            if (stderrText) stderrChunks.push(stderrText)
                            return onFulfilled ? onFulfilled(result) : result
                        },
                        (error) => {
                            const stdoutText = normalizePipeOutput(error?.stdout)
                            const stderrText = normalizePipeOutput(error?.stderr)
                            if (stdoutText) stdoutChunks.push(stdoutText)
                            if (stderrText) stderrChunks.push(stderrText)
                            if (onRejected) return onRejected(error)
                            throw error
                        },
                    )
                }
                const value = target[prop]
                if (typeof value === "function") {
                    return function(...args) {
                        const result = value.apply(target, args)
                        // If the method returns a CommandBuilder (has 'then'), wrap it
                        if (result && typeof result === 'object' && typeof result.then === 'function') {
                            return wrapCommand(result)
                        }
                        return result
                    }
                }
                return value
            },
        })
    }

    const seq$ = (strings, ...values) => {
        const cmd = dax.$(strings, ...values).stdout("piped").stderr("piped")
        return wrapCommand(cmd)
    }

    try {
        const retVal = await run(seq$)
        const stdout = stdoutChunks.join("")
        const stderr = stderrChunks.join("")
        return { retVal, stdout, stderr }
    } finally {
        writeBytes(Deno.stdout, stdoutChunks.join(""))
        writeBytes(Deno.stderr, stderrChunks.join(""))
    }
}