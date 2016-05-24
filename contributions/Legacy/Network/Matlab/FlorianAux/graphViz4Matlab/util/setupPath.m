function gvizPath = setupPath()
% Attempt to add GraphViz to the system path, (temporariliy within the
% matlab session only). 
    gvizPath = 'unknown';
    if ~ispc()
        return
    end
    try  %#ok
        gvizPath = winqueryreg('HKEY_LOCAL_MACHINE','SOFTWARE\AT&T Research Labs\Graphviz', 'InstallPath');
        addtosystempath(fullfile(gvizPath, 'bin'));
    end
end