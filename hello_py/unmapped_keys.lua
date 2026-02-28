

-- unmapped_keys.lua
-- A Lua script to display unmapped keys after a given prefix in a specified mode,
-- visualized in a QWERTY keyboard layout style similar to key-analyzer.nvim.
-- Unmapped keys are marked with an asterisk (*).
-- Usage: Save this file and run in Neovim, e.g., :lua require('unmapped_keys').show('n', '<leader>')

local M = {}

local shift_map = {
    ['!'] = '1',
    ['@'] = '2',
    ['#'] = '3',
    ['$'] = '4',
    ['%'] = '5',
    ['^'] = '6',
    ['&'] = '7',
    ['*'] = '8',
    ['('] = '9',
    [')'] = '0',
    ['_'] = '-',
    ['+'] = '=',
    ['{'] = '[',
    ['}'] = ']',
    ['|'] = '\\',
    [':'] = ';',
    ['"'] = "'",
    ['<'] = ',',
    ['>'] = '.',
    ['?'] = '/',
    ['~'] = '`',
}

local keyboard_rows = {
    {indent = '', keys = {'`', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '='}},
    {indent = ' ', keys = {'q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', '[', ']', '\\'}},
    {indent = '  ', keys = {'a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', ';', "'"}},
    {indent = '   ', keys = {'z', 'x', 'c', 'v', 'b', 'n', 'm', ',', '.', '/'}},
}

local function get_first_base(suffix)
    if #suffix == 0 then return nil end
    local first = suffix:sub(1, 1)
    if first ~= '<' then
        return first
    end
    local endpos = suffix:find('>')
    if not endpos then return nil end
    local keycode = suffix:sub(1, endpos)
    local base = keycode:match('<[%w%-]+(.)>')
    if base then
        return base
    end
    return nil
end

function M.show(mode, prefix)
    mode = mode or 'n'
    prefix = (prefix or '<Leader>'):gsub('<[lL][eE][aA][dD][eE][rR]>', '<Leader>'):gsub('<[lL][oO][cC][aA][lL][lL][eE][aA][dD][eE][rR]>', '<LocalLeader>')

    local maps = vim.api.nvim_get_keymap(mode)
    local used = {}

    for _, map in ipairs(maps) do
        if vim.startswith(map.lhs, prefix) then
            local suffix = map.lhs:sub(#prefix + 1)
            local base = get_first_base(suffix)
            if base then
                local key = base:lower()
                local physical = shift_map[key] or key
                used[physical] = true
            end
        end
    end

    print(string.format('Keyboard analysis for prefix "%s" in mode "%s":', prefix, mode))
    print('Unmapped keys marked with *')
    for _, row in ipairs(keyboard_rows) do
        local line = {}
        for _, key in ipairs(row.keys) do
            local disp = key:upper()
            if not used[key] then
                disp = disp .. '*'
            end
            table.insert(line, disp)
        end
        print(row.indent .. table.concat(line, ' '))
    end
end

return M
