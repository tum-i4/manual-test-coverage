let processId;
let moduleFunctionMap = new Map();
let moduleBaseAddressMap = new Map();
let modulesToInstrument = new Map();
let calledFunctionOffsets = new Map();

const normalizeModuleFunctionMap = (moduleFunctionMap_) => {
    return Object.fromEntries(
        Object.entries(moduleFunctionMap_).map(([key, value]) => [key.toLowerCase(), value])
    );
};

const instrumentModules = () => {
    let numFunctions = 0;
    console.log("Instrumenting " + modulesToInstrument.values().length + " modules...");
    for (const module of modulesToInstrument.values()) {
        const moduleName = module.name.toLowerCase();
        moduleBaseAddressMap.set(moduleName, module.base);
        for (const funcOffset of moduleFunctionMap[moduleName] || []) {
            numFunctions += 1;
            attach_interceptor(moduleName, funcOffset);
        }
    }
    console.log("Done - " + numFunctions + " functions instrumented.");
};

const attach_interceptor = (moduleName, funcOffset) => {
    const funcAddr = moduleBaseAddressMap.get(moduleName).add(funcOffset);

    try {
        Interceptor.attach(funcAddr, function (args) {
            const funcOffsets = calledFunctionOffsets.get(moduleName);
            if (funcOffsets) funcOffsets.add(funcOffset);
            else calledFunctionOffsets.set(moduleName, new Set([funcOffset]));
        });
    }
    catch (err) {
        send({error: `Agent: Could not instrument function ${moduleName}:${funcOffset}`});
    }
};

const instrumentCpp = () => {
    instrumentModules();
};

const setupCpp = (moduleFunctionMap_, pid) => {
    processId = pid;
    moduleFunctionMap = normalizeModuleFunctionMap(moduleFunctionMap_);
    const modules = Object.keys(moduleFunctionMap);
    modulesToInstrument = new ModuleMap(module => modules.includes(module.name.toLowerCase()));

    instrumentCpp();
};

const restoreCpp = () => {
    Interceptor.detachAll();
    instrumentCpp();
};

const clearCppCoverage = () => {
    calledFunctionOffsets.clear();
};

const dumpCppCoverage = () => {
    const calledFunctionOffsetsObject = Object.fromEntries(
        [...calledFunctionOffsets].map(([key, value]) => [key, [...value]])
    );
    send({coverage: calledFunctionOffsetsObject});
};

rpc.exports = {
    setupCpp,
    restoreCpp,
    clearCppCoverage,
    dumpCppCoverage
};
