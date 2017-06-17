#!/bin/bash
#   Original idea and implementation: https://github.com/mikker/dotfiles/blob/master/bin/colortest.sh
#
#   This file echoes a bunch of color codes to the
#   terminal to demonstrate what's available.  Each
#   line is the color code of one forground color,
#   out of 17 (default + 16 escapes), followed by a
#   test use of that color on all nine background
#   colors (default + 8 escapes).
#

T='Co10r'   # The test text

echo -en "\n                    40m       41m       42m       43m\
       44m       45m       46m       47m       49m";

text_colors=( '' '30' '31' '32' \
           '33' '34' '35' \
           '36' '37' '39' \
           '90' '91' '92' \
           '93' '94' '95' \
           '96' '97' )
for text_color in "${text_colors[@]}"
  do
  printf "\n % 5s \033[${text_color}m  $T  " ${text_color}m
  for BG in 40 41 42 43 44 45 46 47 49
  do
    if [ -z $text_color ]; then
        echo -en "$EINS \033[${BG}m  $T  \033[0m";
    else
        echo -en "$EINS \033[$text_color;${BG}m  $T  \033[0m";
    fi
  done
done

echo -en "\n\n\n                   100m      101m      102m      103m      104m\
      105m      106m      107m";
for text_color in "${text_colors[@]}"
  do
  printf "\n % 5s \033[${text_color}m  $T  " ${text_color}m
  for BG in 100 101 102 103 104 105 106 107
  do
    if [ -z $text_color ]; then
        echo -en "$EINS \033[${BG}m  $T  \033[0m";
    else
        echo -en "$EINS \033[$text_color;${BG}m  $T  \033[0m";
    fi
  done
done


echo -en "\n\n\n                    1m        2m        4m        8m       1;2m      1;4m      2;4m";
for text_color in "${text_colors[@]}"
  do
  printf "\n % 5s \033[${text_color}m  $T  " ${text_color}m
  for style in '1' '2' '4' '8' '1;2' '1;4' '2;4'
  do
    if [ -z $text_color ]; then
        echo -en "$EINS \033[${style}m  $T  \033[0m";
    else
        echo -en "$EINS \033[$text_color;${style}m  $T  \033[0m";
    fi
  done
done