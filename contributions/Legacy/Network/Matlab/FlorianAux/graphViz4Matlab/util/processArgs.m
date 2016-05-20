function varargout = processArgs(userArgs, varargin)    
% Process function arguments, allowing args to be passed by
% the user either as name/value pairs, or positionally, or both. 
%
% This function also provides optional enforcement of required inputs, and 
% optional type checking. Argument names must start with the '-'
% character and not precede any positional arguments. 
%
% Matthew Dunham
% University of British Columbia
% Last updated January 14th, 2010
%
%% USAGE:
%
% [out1,out2,...,outN] = processArgs(userArgs ,...
% '-name1' , default1                         ,...
% '-name2' , default2                         ,...
% '-nameN' , defaultN                         );
% 
% The 'userArgs' input is a cell array and in normal usage is simply the
% varargin cell array from the calling function. It contains 0 to N values
% or 0 to N name/value pairs. It may also contain a combination of
% positional and named arguments as long as no named argument precedes a
% positional one. 
%
% Note, this function is CASE INSENSITIVE. 
%
%% ENFORCING REQUIRED ARGUMENTS
%
% To ensure that certain arguments are passed in, (and error if not), add a
% '*' character to the corresponding name as in
%
% [out1,...] = processArgs(userArgs,'*-name1',default1,...
%
%
% Providing empty values, (e.g. {},[],'') for required arguments also
% errors unless these were explicitly passed as named arguments. 
%% TYPE CHECKING
%
% To enforce that the input type, (class) is the same type as the default
% value, add a '+' character to the corresponding name as in
%
% [out1,...] = processArgs(userArgs,'+-name1',default1,...
%
% '+' and '*' can be combined as in
%
% [out1,...] = processArgs(userArgs,'*+-name1',default1,...
%
% or equivalently
%
% [out1,...] = processArgs(userArgs,'+*-name1',default1,...
%% OTHER CONSIDERATIONS
%
% If the user passes in arguments in positional mode, and uses [], {}, or
% '' as place holders, the default values are used in their place. When the
% user passes in values via name/value pairs, this behavior does not
% occur; the explicit value the user specified, (even if [], {}, '') is
% always used. 
%
%% ADVANCED
% The programmer must specify the same number of output arguments as
% possible input arguments, OR exactly one output. If exactly one output
% is used, the outputs are all bundled into a single cell array and
% returned with each arg value preceded by its name. This can be useful for
% relaying some or all of the arguments to subsequent functions as is done
% with the extractArgs function.
%
%% DEPENDENCIES
%
% None
%
%% EXAMPLES
% These are all valid usages. Note that here the first and second arguments
% are required and the types of the second and fourth arguments are
% checked. 
%
% outerFunction(obj,...
%                 '-first'  , 1         ,...
%                 '-second' , MvnDist() ,...
%                 '-third'  , 22        ,...
%                 '-fourth' , 10        ); 
%
% outerFunction(obj,'-fourth',3,'-second',MvnDist(),'-first',12);
% outerFunction(obj,1,MvnDist(),3);
% outerFunction(obj,1,MvnDist(),3,[]);                           
% outerFunction(obj,'-first',1,'-second',DiscreteDist(),'-third',[]);
% outerFunction(obj,1,MvnDist(),'-fourth',10);                           
% 
% 
% function [a,b,c,d] = outerFunction(obj,varargin)
%   [a,b,c,d] = processArgs(varargin ,...
%   '*-first'       , []             ,...
%   '*+-second'     , MvnDist()      ,...
%   '-third'        , 18             ,...
%   '+-fourth'      , 23             );
% end 
%%  CONSTANTS
    PREFIX = '-';  % prefix that must precede the names of arguments. 
    REQ    = '*';  % require the argument
    TYPE   = '+';  % check the type of the arg against the default type
    
    % set to true for more exhaustive error checking or false for faster
    % execution.
    FULL_ERROR_CHECK = true; 

%% PROCESS VARARGIN - PASSED BY PROGRAMMER
    
    %% Check Initial Inputs
    if ~iscell(userArgs)                                                   ,throwAsCaller(MException('PROCESSARGS:noUserArgs','PROGRAMMER ERROR - you must pass in the user''s arguments in a cell array as in processArgs(varargin,''-name'',val,...)'));end
    if isempty(varargin)                                                   ,throwAsCaller(MException('PROCESSARGS:emptyVarargin','PROGRAMMER ERROR - you have not passed in any name/default pairs to processArgs'));  end
    %% Extract Programmer Argument Names and Markers
    progArgNames  = varargin(1:2:end);
    maxNargs  = numel(progArgNames);
    required  = cellfun(@(c)any(REQ==c(1:min(3,end))),progArgNames);
    typecheck = cellfun(@(c)any(TYPE==c(1:min(3,end))),progArgNames); 
    if ~iscellstr(progArgNames)                                            ,throwAsCaller(MException('PROCESSARGS:notCellStr ',sprintf('PROGRAMMER ERROR - you must pass to processArgs name/default pairs'))); end
    %% Remove * and + Markers
    try
    progArgNames(required | typecheck)  =    ...
        cellfuncell(@(c)c(c~=REQ & c~=TYPE) ,...
             progArgNames(required | typecheck));
    catch ME
       if strcmp(ME.identifier,'MATLAB:UndefinedFunction')
                                                                           err = MException('PROCESSARGS:missingExternalFunctions','ProcessArgs requires the following external functions available in PMTK2: catString, cellfuncell, interweave, isprefix. Please add these to your MATLAB path.'); 
           throw(addCause(err,ME));
       else
           rethrow(ME);
       end
    end
    %% Set Default Values
    defaults = varargin(2:2:end);
    varargout = defaults;
    %% Check Programmer Supplied Arguments
    if mod(numel(varargin),2)                                              ,throwAsCaller(MException('PROCESSARGS:oddNumArgs',sprintf('PROGRAMMER ERROR - you have passed in an odd number of arguments to processArgs, which requires name/default pairs')));  end
    if any(cellfun(@isempty,progArgNames))                                 ,throwAsCaller(MException('PROCESSARGS:emptyStrName ',sprintf('PROGRAMMER ERROR - empty-string names are not allowed')));end
    if nargout ~= 1 && nargout ~= maxNargs                                 ,throwAsCaller(MException('PROCESSARGS:wrongNumOutputs',sprintf('PROGRAMMER ERROR - processArgs requires the same number of output arguments as named/default input pairs'))); end
    if ~isempty(PREFIX)             && ...
       ~all(cellfun(@(c)~isempty(c) &&...
        c(1)==PREFIX,progArgNames)) 
                                                                            throwAsCaller(MException('PROCESSARGS:missingPrefix',sprintf('PROGRAMMER ERROR - processArgs requires that each argument name begin with the prefix %s',PREFIX))); 
    end
    if FULL_ERROR_CHECK  && ...
       numel(unique(progArgNames)) ~= numel(progArgNames)                  ,throwAsCaller(MException('PROCESSARGS:duplicateName',sprintf('PROGRAMMER ERROR - you can not use the same argument name twice')));end
%% PROCESS USERARGS

    %% Error Check User Args
    if numel(userArgs) == 0 && nargout > 1
        if any(required)                                                   ,throwAsCaller(MException('PROCESSARGS:missingReqArgs',sprintf('The following required arguments were not specified:\n%s',catString(progArgNames(required))))); 
        else  return;
        end
    end
    if FULL_ERROR_CHECK 
     % slow, but helpful in transition from process_options to processArgs
     % checks for missing '-' 
        if ~isempty(PREFIX)
            userstrings = lower(...
                userArgs(cellfun(@(c)ischar(c) && size(c,1)==1,userArgs)));
            problem = ismember(...
                userstrings,cellfuncell(@(c)c(2:end),progArgNames));
            if any(problem)
                if sum(problem) == 1,                                       warning('processArgs:missingPrefix','The specified value ''%s'', matches an argument name, except for a missing prefix %s. It will be interpreted as a value, not a name.',userstrings{problem},PREFIX)
                else                                                        warning('processArgs:missingPrefix','The following values match an argument name, except for missing prefixes %s:\n\n%s\n\nThey will be interpreted as values, not names.',PREFIX,catString(userstrings(problem)));
                end
            end
        end
    end
    %% Find User Arg Names
    userArgNamesNDX = find(cellfun(@(c)ischar(c)  &&...
                                      ~isempty(c) &&...
                                      c(1)==PREFIX,userArgs));
    %% Check User Arg Names                                  
    if ~isempty(userArgNamesNDX) && ...
       ~isequal(userArgNamesNDX,userArgNamesNDX(1):2:numel(userArgs)-1)
        if isempty(PREFIX),                                                 throwAsCaller(MException('PROCESSARGS:missingVal',sprintf('\n(1) every named argument must be followed by its value\n(2) no positional argument may be used after the first named argument\n')));
        else                                                                throwAsCaller(MException('PROCESSARGS:posArgAfterNamedArg',sprintf('\n(1) every named argument must be followed by its value\n(2) no positional argument may be used after the first named argument\n(3) every argument name must begin with the ''%s'' character\n(4) values cannot be strings beginning with the %s character\n',PREFIX,PREFIX))); 
        end
    end
     if FULL_ERROR_CHECK          && ...
        ~isempty(userArgNamesNDX) && ...
         numel(unique(userArgs(userArgNamesNDX))) ~= numel(userArgNamesNDX)
                                                                            throwAsCaller(MException('PROCESSARGS:duplicateUserArg',sprintf('You have specified the same argument name twice')));
     end
    %% Extract Positional Args 
    argsProvided = false(1,maxNargs);
    if isempty(userArgNamesNDX)
        positionalArgs = userArgs;
    elseif userArgNamesNDX(1) == 1
        positionalArgs = {};
    else
        positionalArgs = userArgs(1:userArgNamesNDX(1)-1); 
    end
    %% Check For Too Many Inputs
    if numel(positionalArgs) + numel(userArgNamesNDX) > maxNargs           ,throwAsCaller(MException('PROCESSARGS:tooManyInputs',sprintf('You have specified %d too many arguments to the function',numel(positionalArgs)+numel(userArgNamesNDX)- maxNargs)));end
    %% Process Positional Args
    for i=1:numel(positionalArgs)
    % don't overwrite default value if positional arg is 
    % empty, i.e. '',{},[]    
        if ~isempty(userArgs{i})  
           argsProvided(i) = true;
           if typecheck(i) && ~isa(userArgs{i},class(defaults{i}))         ,throwAsCaller(MException('PROCESSARGS:argWrongType',sprintf('Argument %d must be of type %s',i,class(defaults{i}))));  end
           varargout{i} = userArgs{i};
        end
    end
    %% Process Named Args
    userArgNames = userArgs(userArgNamesNDX);
    userProgMap = zeros(1,numel(userArgNames));
    usedProgArgNames = false(1,numel(progArgNames));
    for i=1:numel(userArgNames)
       for j=1:numel(progArgNames)
          if ~usedProgArgNames(j) && strcmpi(userArgNames{i},progArgNames{j})
              userProgMap(i) = j;
              usedProgArgNames(j) = true;
              break;
          end
       end
    end
    %% Error Check User Args
    if any(~userProgMap)                                                   ,throwAsCaller(MException('PROCESSARGS:invalidArgNames',sprintf('The following argument names are invalid: %s',catString(userArgNames(userProgMap == 0),' , ')))); end
    if any(userProgMap  <= numel(positionalArgs))                          ,throwAsCaller(MException('PROCESSARGS:bothPosAndName' ,sprintf('You cannot specify an argument positionally, and by name in the same function call.')));end
    %% Extract User Values
    userValues = userArgs(userArgNamesNDX + 1);
    %% Type Check User Args
    if any(typecheck)
       for i=1:numel(userArgNamesNDX)
          if typecheck(userProgMap(i)) && ...
             ~isa(userArgs{userArgNamesNDX(i)+1},...
              class(defaults{userProgMap(i)}))
                                                                            throwAsCaller(MException('PROCESSARGS:wrongType',sprintf('Argument %s must be of type %s',userArgs{userArgNamesNDX(i)},class(defaults{userProgMap(i)})))); 
          end
       end
    end    
    varargout(userProgMap) = userValues;
    %% Check Required Args
    argsProvided(userProgMap) = true;
    if any(~argsProvided & required)                                       ,throwAsCaller(MException('PROCESSARGS:emptyVals',sprintf('The following required arguments were either not specified, or were given empty values:\n%s',catString(progArgNames(~argsProvided & required))))); end
    %% Relay Mode
    if nargout == 1 && (numel(varargin) > 2 || (numel(varargin) == 1 && isprefix('-',varargin{1})))
        varargout = {interweave(progArgNames,varargout)};
    end 
    
end


function s = catString(c,delim)
% Converts a cell array of strings to a single string, (i.e. single-row
% character array). The specified delimiter, delim, is added between each
% entry. Include any spaces you want in delim. If delim is not specified,
% ', ' is used instead. If c is already a string, it is just returned. If c
% is empty, s = ''. 
%
% EXAMPLE:
%
% s = catString({'touch /tmp/foo';'touch /tmp foo2';'mkdir /tmp/test'},' && ')
% s =
% touch /tmp/foo && touch /tmp foo2 && mkdir /tmp/test

   if nargin == 0; s = ''; return; end
   if ischar(c), s=c; 
        if strcmp(s,','),s = '';end
       return; 
   end
   if isempty(c),s=''; return;end
   if nargin < 2, delim = ',  '; end
   s = '';
   for i=1:numel(c)
      s = [s, rowvec(c{i}),rowvec(delim)]; %#ok
   end
    s(end-numel(delim)+1:end) = [];
    if strcmp(s,','),s = '';end
end
    
    
function out = cellfuncell(fun, C, varargin)
    out = cellfun(fun, C, varargin{:},'UniformOutput',false);
end
    
function C = interweave(A,B)
% If A, B are two cell arrays of length N1, N2, C is a cell array of length
% N1 + N2 where where C(1) = A(1), C(2) = B(1), C(3) = A(2), C(4) = B(2), ... etc
% Note, C is always a row vector. If one cell array is longer than the 
% other the remaining elements of the longer cell array are added to the
% end of C. A and B are first converted to column vectors. 
    A = A(:); B = B(:);
    C = cell(length(A)+length(B),1);
    counter = 1;
    while true
       if ~isempty(A)
          C(counter) = A(1); A(1) = [];
          counter = counter + 1;
       end
       if ~isempty(B)
           C(counter) = B(1); B(1) = [];
           counter = counter + 1;
       end
       if isempty(A) && isempty(B)
           break;
       end
    end
    C = C';
end    
    
function p = isprefix(short,long)
% ISPREFIX Tests if the first arg is a prefix of the second. 
% The second arg may also be a cell array of strings, in which case, each
% is tested. CASE SENSITIVE!
%
% If the second argument is not a string, p = false, it does not error. 
%
% EXAMPLES:
% 
% isprefix('foo','foobar')
% ans =
%      1
%
%isprefix('test_',{'test_MvnDist','test_DiscreteDist','UnitTest'})
%ans =
%     1     1     0
    error(nargchk(2,2,nargin));
    if ischar(long)
        p = strncmp(long,short,length(short));
    elseif iscell(long)
        p = cellfun(@(c)isprefix(short,c),long);
    else
        p  = false;
    end
end    
    
    
function x = rowvec(x)
    x = x(:)';
end    
    
function x = colvec(x)
    x = x(:);
end











