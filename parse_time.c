#include <stdio.h>
#include <string.h>

const char char_zero = 48;
const char char_nine = 57;

int parse_int_from_char_array(char *chars, int *val, int str_len,
                              char char_start, int idx0, int idx1)
// Parse an integer from positions idx0:idx1 (inclusive) within chars.
//
// Example: "2020-01-24"
//                  ^^^
//           0123456789
//
// int day, status;
// status = parse_int_from_char_array("2020-01-24", &day, 10, '-', 7, 9);
//
// Args:
//  char *chars: time string
//  int *val: output value
//  int str_len: length of *chars string
//  char char_start: optional character at position idx0 when char_start > 0
//  int idx0: start index for parsing integer
//  int idx1: stop index (inclusive) for parsing integer
{
    int mult = 1;
    char digit;
    char ch;
    int status = 0;

    *val = 0;

    // Check if string ends (has 0x00) before str_len.
    for (size_t i = idx0; i <= idx1; i++) {
        if (chars[i] == 0) {
            str_len = i;
            break;
        }
    }

    // String ends at exactly before the beginning of requested value,
    // e.g. "2000-01" (str_len=7) for day (idx0=7). This is OK in some
    // cases, e.g. before hour (2000-01-01).
    if (idx0 == str_len) {
        return -1;
    }

    // String ends in the middle of requested value. This implies a badly
    // formatted time.
    if (idx1 >= str_len) {
        return -2;
    }

    // Look for optional start character, e.g. ':' before minute. If char_start == 0
    // then no character is required.
    if (char_start > 0) {
        // Required start character not found.
        if (chars[idx0] != char_start) {
            return -3;
        }
        idx0 += 1;
    }
    // Build up the value using reversed digits
    for (int ii = idx1; ii >= idx0; ii--)
    {
        ch = chars[ii];
        if (ch < char_zero || ch > char_nine) {
            // Not a digit, implying badly formatted time.
            return -4;
        }
        digit = ch - char_zero;
        *val += digit * mult;
        mult *= 10;
    }

    return 0;
}

int parse_frac_from_char_array(char *chars, double *val,
                               int str_len, char char_start, int idx0)
// Parse trailing fraction starting from position idx0 in chars.
//
// Example: "2020-01-24T12:13:14.5556"
//                              ^^^^^
//           012345678901234567890123
//
// int status;
// float frac;
// status = parse_frac_from_char_array("2020-01-24T12:13:14.5556", &frac, 24, '.', 19);
//
// Args:
//  char *chars: time string
//  double *val: output fraction value
//  int str_len: length of *chars string
//  char char_start: optional character at position idx0 when char_start > 0
//  int idx0: start index for parsing fraction
{
    double mult = 0.1;
    char digit;
    char ch;
    int status = 0;

    *val = 0.0;

    // String ends at exactly before the beginning of requested fraction.
    // e.g. "2000-01-01 12:13:14". Fraction value is zero.
    if (idx0 == str_len) {
        return 0;
    }

    // Look for optional start character, e.g. '.' before fraction. If char_start == 0
    // then no character is required. This can happen for unusual formats like
    // Chandra GRETA time yyyyddd.hhmmssfff.
    if (char_start > 0) {
        // Required start character not found.
        if (chars[idx0] != char_start) {
            return -3;
        }
        idx0 += 1;
    }

    for (size_t ii = idx0; ii < str_len; ii++)
    {
        ch = chars[ii];
        if (ch < char_zero || ch > char_nine) {
            // Not a digit, implying badly formatted time.
            return -4;
        }
        digit = ch - char_zero;
        *val += digit * mult;
        mult /= 10.0;
    }
    return 0;
}

int parse_iso_time(char *time, int max_str_len, /* char sep, */
                   int *year, int *month, int *day, int *hour,
                   int *minute, double *second)
// Parse an ISO time in `chars`.
//
// Example: "2020-01-24T12:13:14.5556"
//
// Args:
//  char *time: time string
//  int max_str_len: max length of string (may be null-terminated before this)
//  // char sep: separator between date and time (normally ' ' or 'T')
//  int *year, *month, *day, *hour, *minute: output components (ints)
//  double *second: output seconds
//
// Returns:
//  int status: 0 for OK, < 0 for not OK
{
    int str_len;
    int status = 0;
    int isec;
    double frac;
    char sep = ' ';
    *month = 1;
    *day = 1;
    *hour = 0;
    *minute = 0;
    *second = 0.0;

    // Parse "2000-01-12 13:14:15.678"
    //        01234567890123456789012

    // Check for null termination before max_str_len. If called using a contiguous
    // numpy 2-d array of chars there may or may not be null terminations.
    str_len = max_str_len;
    for (size_t i = 0; i < max_str_len; i++) {
        if (time[i] == 0) {
            str_len = i;
            break;
        }
    }

    status = parse_int_from_char_array(time, year, str_len, 0, 0, 3);
    if (status < 0) { return status; }

    status = parse_int_from_char_array(time, month, str_len, '-', 4, 6);
    if (status == -1) { return 0; }  // "2000" is OK
    else if (status < 0) { return status; }

    status = parse_int_from_char_array(time, day, str_len, '-', 7, 9);
    // Any problems here indicate a bad date. "2000-01" is NOT OK.
    if (status < 0) { return status; }

    status = parse_int_from_char_array(time, hour, str_len, sep, 10, 12);
    if (status == -1) { return 0; }  // "2000-01-02" is OK
    else if (status < 0) { return status; }

    status = parse_int_from_char_array(time, minute, str_len, ':', 13, 15);
    // Any problems here indicate a bad date. "2000-01-02 12" is NOT OK.
    if (status < 0) { return status; }

    status = parse_int_from_char_array(time, &isec, str_len, ':', 16, 18);
    if (status == -1) { return 0; }  // "2000-01-02 12:13" is OK
    else if (status < 0) { return status; }

    status = parse_frac_from_char_array(time, &frac, str_len, '.', 19);
    if (status < 0) { return status; }

    *second = isec + frac;

    return 0;
}

int main(int argc, char *argv[])
{
    int status;
    char minus = '-';
    int year, mon, day, hour, min;
    double sec;
    int str_len;

    str_len = strlen(argv[1]);
    status = parse_iso_time(argv[1], str_len, &year, &mon, &day, &hour, &min, &sec);
    if (status != 0) {
        printf("ERROR: status = %d\n", status);
        return status;
    } else {
        printf("%d %d %d %d %d %f\n", year, mon, day, hour, min, sec);
    }

    printf("Start 10 million loops\n");
    for (size_t i = 0; i < 10000000; i++)
    {
            status = parse_iso_time(argv[1], str_len, &year, &mon, &day, &hour, &min, &sec);
    }
    printf("Done\n");

    return status;
}
