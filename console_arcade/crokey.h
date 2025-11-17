/*
MIT License

Copyright (c) 2021 remoof (https://codeberg.org/remoof/crokey)

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
*/

#include <stdio.h>
#include <string.h>

#ifndef CROKEY_INCLUDE
#define CROKEY_INCLUDE

#define KEY_LIST \
    X(KEY_SPACE) \
    X(KEY_APOSTROPHE) \
    X(KEY_COMMA) \
    X(KEY_MINUS) \
    X(KEY_PERIOD) \
    X(KEY_SLASH) \
    X(KEY_0) \
    X(KEY_1) \
    X(KEY_2) \
    X(KEY_3) \
    X(KEY_4) \
    X(KEY_5) \
    X(KEY_6) \
    X(KEY_7) \
    X(KEY_8) \
    X(KEY_9) \
    X(KEY_SEMICOLON) \
    X(KEY_EQUAL) \
    X(KEY_A) \
    X(KEY_B) \
    X(KEY_C) \
    X(KEY_D) \
    X(KEY_E) \
    X(KEY_F) \
    X(KEY_G) \
    X(KEY_H) \
    X(KEY_I) \
    X(KEY_J) \
    X(KEY_K) \
    X(KEY_L) \
    X(KEY_M) \
    X(KEY_N) \
    X(KEY_O) \
    X(KEY_P) \
    X(KEY_Q) \
    X(KEY_R) \
    X(KEY_S) \
    X(KEY_T) \
    X(KEY_U) \
    X(KEY_V) \
    X(KEY_W) \
    X(KEY_X) \
    X(KEY_Y) \
    X(KEY_Z) \
    X(KEY_BACKSLASH) \
    X(KEY_GRAVE) \
    X(KEY_LBRACE) \
    X(KEY_RBRACE) \
    X(KEY_BACKSPACE) \
    X(KEY_TAB) \
    X(KEY_RETURN) \
    X(KEY_ESCAPE) \
    X(KEY_HOME) \
    X(KEY_LEFT) \
    X(KEY_UP) \
    X(KEY_RIGHT) \
    X(KEY_DOWN) \
    X(KEY_PAGEUP) \
    X(KEY_PAGEDOWN) \
    X(KEY_INSERT) \
    X(KEY_KP_MULTIPLY) \
    X(KEY_KP_ADD) \
    X(KEY_KP_SUBTRACT) \
    X(KEY_KP_DIVIDE) \
    X(KEY_KP_0) \
    X(KEY_KP_1) \
    X(KEY_KP_2) \
    X(KEY_KP_3) \
    X(KEY_KP_4) \
    X(KEY_KP_5) \
    X(KEY_KP_6) \
    X(KEY_KP_7) \
    X(KEY_KP_8) \
    X(KEY_KP_9) \
    X(KEY_F1) \
    X(KEY_F2) \
    X(KEY_F3) \
    X(KEY_F4) \
    X(KEY_F5) \
    X(KEY_F6) \
    X(KEY_F7) \
    X(KEY_F8) \
    X(KEY_F9) \
    X(KEY_F10) \
    X(KEY_F11) \
    X(KEY_F12) \
    X(KEY_LSHIFT) \
    X(KEY_RSHIFT) \
    X(KEY_LCONTROL) \
    X(KEY_RCONTROL) \
    X(KEY_CAPSLOCK) \
    X(KEY_LMETA) \
    X(KEY_RMETA) \
    X(KEY_LALT) \
    X(KEY_RALT)  \
    X(KEY_DELETE) \
    X(KEY_LIST_SPLIT) \
    X(BUTTON_1) \
    X(BUTTON_2) \
    X(BUTTON_3) \
    X(BUTTON_4) \
    X(BUTTON_5) \
    X(KEY_LIST_NONE)


enum crokey_key {
#define X(x) x,
    KEY_LIST
#undef X
};

enum crokey_key crokey_num_to_enum(size_t num);
char* crokey_enum_to_string(enum crokey_key key);
enum crokey_key crokey_get_pressed_key(void);

#endif // CROKEY_INCLUDE

#ifdef CROKEY_IMPL

enum crokey_key crokey_num_to_enum(size_t num) {
    switch(num) {
#define X(x) case x: return x;
    KEY_LIST
#undef X
    default:
        return KEY_LIST_NONE;
    }
}

char* crokey_enum_to_string(enum crokey_key key) {
    static char key_string[16] = "None";

    switch(key) {
#define X(x) case x: {strcpy(key_string, #x); return key_string;}
    KEY_LIST
#undef X
    default:
        strcpy(key_string, "None");
        return key_string;
    }
}

#ifdef __linux__

#include <X11/Xlib.h>
#include <X11/keysym.h>
#include <stdlib.h>

enum crokey_key crokey_get_pressed_key(void) {
    static int display_init = 1;

    static Display *display;
    static Window window;
    static char keys_return[32];
    static KeyCode key_array[KEY_LIST_SPLIT];

    // defined in usr/include/X11/keysymdef.h
    static const int sym_array[] = {
        0x0020, 0x0027, 0x002c, 0x002d, 0x002e,
        0x002f, 0x0030, 0x0031, 0x0032, 0x0033,
        0x0034, 0x0035, 0x0036, 0x0037, 0x0038,
        0x0039, 0x003b, 0x003d, 0x0041, 0x0042,
        0x0043, 0x0044, 0x0045, 0x0046, 0x0047,
        0x0048, 0x0049, 0x004a, 0x004b, 0x004c,
        0x004d, 0x004e, 0x004f, 0x0050, 0x0051,
        0x0052, 0x0053, 0x0054, 0x0055, 0x0056,
        0x0057, 0x0058, 0x0059, 0x005a, 0x005c,
        0x0060, 0x007b, 0x007d, 0xff08, 0xff09,
        0xff0d, 0xff1b, 0xff50, 0xff51, 0xff52,
        0xff53, 0xff54, 0xff55, 0xff56, 0xff63,
        0xffaa, 0xffab, 0xffad, 0xffaf, 0xffb0,
        0xffb1, 0xffb2, 0xffb3, 0xffb4, 0xffb5,
        0xffb6, 0xffb7, 0xffb8, 0xffb9, 0xffbe,
        0xffbf, 0xffc0, 0xffc1, 0xffc2, 0xffc3,
        0xffc4, 0xffc5, 0xffc6, 0xffc7, 0xffc8,
        0xffc9, 0xffe1, 0xffe2, 0xffe3, 0xffe4,
        0xffe5, 0xffe7, 0xffe8, 0xffe9, 0xffea,
        0xffff,                                };

    // avoid opening multiple displays and windows
    if(display_init) {
        display = XOpenDisplay(NULL);
        if(display == NULL) {
            fputs("Cannot open display\n", stderr);
            exit(EXIT_FAILURE);
        }

        window = XDefaultRootWindow(display);

        for(size_t i = 0; i < KEY_LIST_SPLIT; i++) {
            key_array[i] = XKeysymToKeycode(display, sym_array[i]);
        }

        display_init = 0;
    }

    XQueryKeymap(display, keys_return);
    for(size_t i = 0; i < KEY_LIST_SPLIT; i++) {
        short compare_result = (keys_return[key_array[i]>>3] & (1<<(key_array[i]&7)));
        if(compare_result) {
            return crokey_num_to_enum(i);
        }
    }


    static unsigned int mask;
    {
        static Window root_x;
        static Window root_y;
        static int win_x;
        static int win_y;
        static int root_return;
        static int child_return;
        XQueryPointer(display, window, &root_x, &root_y, &win_x, &win_y, &root_return, &child_return, &mask);
    }

     switch(mask) {
        case Button1Mask:
            return BUTTON_1;
        case Button2Mask:
            return BUTTON_2;
        case Button3Mask:
            return BUTTON_3;
        case Button4Mask:
            return BUTTON_4;
        case Button5Mask:
            return BUTTON_5;
    }
    return KEY_LIST_NONE;
}

#endif // __linux__

#ifdef _WIN32

#include <Windows.h>

enum crokey_key crokey_get_pressed_key(void) {
    // https://docs.microsoft.com/en-us/windows/win32/inputdev/virtual-key-codes
    static const int key_array[] = {
        0x20, 0xDE, 0xBC, 0xBD, 0xBE,
        0xBF, 0x30, 0x31, 0x32, 0x33,
        0x34, 0x35, 0x36, 0x37, 0x38,
        0x39, 0xBA, 0xBB, 0x41, 0x42,
        0x43, 0x44, 0x45, 0x46, 0x47,
        0x48, 0x49, 0x4A, 0x4B, 0x4C,
        0x4D, 0x4E, 0x4F, 0x50, 0x51,
        0x52, 0x53, 0x54, 0x55, 0x56,
        0x57, 0x58, 0x59, 0x5A, 0xDC,
        0xC0, 0xDB, 0xDD, 0x08, 0x09,
        0x0D, 0x1B, 0x24, 0x25, 0x26,
        0x27, 0x28, 0x21, 0x22, 0x2D,
        0x6A, 0x6B, 0x6D, 0x6F, 0x60,
        0x61, 0x62, 0x63, 0x64, 0x65,
        0x66, 0x67, 0x68, 0x69, 0x70,
        0x71, 0x72, 0x73, 0x74, 0x75,
        0x76, 0x77, 0x78, 0x79, 0x7A,
        0x7B, 0xA0, 0xA1, 0xA2, 0xA3,
        0x14, 0x5B, 0x5C, 0xA4, 0xA5,
        0x2E,                        };

        for(size_t i = 0; i < KEY_LIST_SPLIT; i++) {
            if(GetAsyncKeyState(key_array[i]) < 0) {
                return crokey_num_to_enum(i);
            }
        }

        if(GetAsyncKeyState(VK_LBUTTON) < 0) {
            return BUTTON_1;
        }

        if(GetAsyncKeyState(VK_RBUTTON) < 0) {
            return BUTTON_2;
        }

        if(GetAsyncKeyState(VK_MBUTTON) < 0) {
            return BUTTON_3;
        }

        if(GetAsyncKeyState(VK_XBUTTON1) < 0) {
            return BUTTON_4;
        }

        if(GetAsyncKeyState(VK_XBUTTON2) < 0) {
            return BUTTON_5;
        }

        return KEY_LIST_NONE;
}

#endif // _WIN32

#ifdef __APPLE__

#include <AppKit/AppKit.h>
#include <stdint.h>

enum crokey_key crokey_get_pressed_key(void) {
    // https://stackoverflow.com/a/16125341
    static const uint16_t key_array[] = {
        0x31, 0x27, 0x2B, 0x1B, 0x2F,
        0x2C, 0x1D, 0x12, 0x13, 0x14,
        0x15, 0x17, 0x16, 0x1A, 0x1C,
        0x19, 0x29, 0x18, 0x00, 0x0B,
        0x08, 0x02, 0x0E, 0x03, 0x05,
        0x04, 0x22, 0x26, 0x28, 0x25,
        0x2E, 0x2D, 0x1F, 0x23, 0x0C,
        0x0F, 0x01, 0x11, 0x20, 0x09,
        0x0D, 0x07, 0x10, 0x06, 0x2A,
        0x32, 0x21, 0x1E, 0x33, 0x30,
        0x24, 0x35, 0x73, 0x7b, 0x7E,
        0x7C, 0x7D, 0x74, 0x79, 0x72,
        0x43, 0x45, 0x4E, 0x4B, 0x52,
        0x53, 0x54, 0x55, 0x56, 0x57,
        0x58, 0x59, 0x5B, 0x5C, 0x7A,
        0x78, 0x63, 0x76, 0x60, 0x61,
        0x62, 0x64, 0x65, 0x6D, 0x67,
        0x6F, 0x38, 0x3C, 0x3B, 0x3E,
        0x39, 0x37, 0x37, 0x3A, 0x3D,
        0x75,                        };

    static int32_t state_id = 0;

    for(size_t i = 0; i < KEY_LIST_SPLIT; i++) {
       if(CGEventSourceKeyState(state_id, key_array[i])) {
           return crokey_num_to_enum(i);
       }
    }

    if(CGEventSourceButtonState(state_id, 0ul) {
        return BUTTON_1;
    }

    if(CGEventSourceButtonState(state_id, 1ul) {
        return BUTTON_2;
    }

    if(CGEventSourceButtonState(state_id, 2ul) {
        return BUTTON_3;
    }

    if(CGEventSourceButtonState(state_id, 3ul) {
        return BUTTON_4;
    }

    if(CGEventSourceButtonState(state_id, 4ul) {
        return BUTTON_5;
    }

    return KEY_LIST_NONE;
}

#endif // __APPLE__

#endif // CROKEY_IMPL

