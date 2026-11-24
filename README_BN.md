# FunWithFriend — Render Free Web Service

## গুরুত্বপূর্ণ
এই বট TikTok-এ কৃত্রিম লাইক/ভিউ তৈরি করে না। এটি ব্যক্তিগতভাবে TikTok লিংক গ্রহণ করে Telegram-এ বন্ধুদের সাথে শেয়ার করার সুবিধা দেয়।

Render-এর Free Web Service ১৫ মিনিট ইনবাউন্ড ট্রাফিক না পেলে sleep করতে পারে। তাই এটি সবসময় তাৎক্ষণিকভাবে সাড়া দেবে—এমন নিশ্চয়তা নেই। Free Background Worker পাওয়া যায় না।

## ১) GitHub
এই ফোল্ডারের সব ফাইল একটি নতুন GitHub repository-তে upload করো।

## ২) Telegram User ID
Telegram-এ @userinfobot খুলে `/start` পাঠিয়ে নিজের numeric User ID জেনে নাও।

## ৩) Render
1. https://dashboard.render.com/ এ লগইন করো।
2. New → Web Service নির্বাচন করো।
3. GitHub repository connect করো।
4. Runtime: Python
5. Build Command: `pip install -r requirements.txt`
6. Start Command: `gunicorn app:app`
7. Instance Type: Free

## ৪) Environment Variables
Render-এর Environment tab-এ এই তিনটি variable যোগ করো:

- `BOT_TOKEN` = BotFather থেকে পাওয়া token
- `ADMIN_USER_ID` = নিজের Telegram numeric User ID
- `WEBHOOK_SECRET` = কমপক্ষে 32 অক্ষরের একটি এলোমেলো গোপন string

`RENDER_EXTERNAL_URL` Render নিজে সেট করে।

Token কখনো GitHub-এ বা চ্যাটে প্রকাশ করবে না। ভুল করে প্রকাশ করলে BotFather থেকে token revoke করে নতুন token নেবে।

## ৫) Deploy
Create Web Service চাপো। Deploy শেষ হলে Render-এর URL খুলে `FunWithFriend is running` দেখা উচিত। তারপর Telegram-এ নিজের বট খুলে `/start` পাঠাও।

## সীমাবদ্ধতা
এই starter version-এর `/stats` শুধু চলতি process-এর RAM-এ থাকা link গুনে; restart/sleep/redeploy হলে count reset হবে। স্থায়ী history চাইলে persistent database যোগ করতে হবে।
