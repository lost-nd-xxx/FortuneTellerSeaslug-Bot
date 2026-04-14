import subprocess
import os
import requests
import sys

#栞を呼び出して投稿メッセージを取得する
def get_message(shiori):
	dlldir = os.getcwd()
	if shiori == 'yaya':
		dllpath = r'shiori\yaya\yaya.dll'
		dlldir += r'\shiori\yaya\\'
		enc = 'utf-8'
	elif shiori == 'kawari':
		dllpath = r'shiori\kawari\shiori.dll'
		dlldir += r'\shiori\kawari\\'
		enc = 'shift_jis'
	else:
		dllpath = r'shiori\satori\satori.dll'
		dlldir += r'\shiori\satori\\'
		enc = 'shift_jis'
	s = ''
	subprocess.run(fr'shioricaller\shioricaller.exe {dllpath} {dlldir} < shioricaller\request.txt > shioricaller\response.txt', shell=True)
	with open(r'shioricaller\response.txt', encoding=enc) as f:
		for line in f:
			if line.startswith('Value: '):
				s = line[7:]
				break
	s = s.replace(r'\n', '\n')
	return s

#栞を呼び出してメンション返信メッセージ（占いあり）を取得する
def get_message_for_mention(shiori):
	dlldir = os.getcwd()
	if shiori == 'yaya':
		dllpath = r'shiori\yaya\yaya.dll'
		dlldir += r'\shiori\yaya\\'
		enc = 'utf-8'
	s = ''
	subprocess.run(fr'shioricaller\shioricaller.exe {dllpath} {dlldir} < shioricaller\mention_request.txt > shioricaller\response.txt', shell=True)
	with open(r'shioricaller\response.txt', encoding=enc) as f:
		for line in f:
			if line.startswith('Value: '):
				s = line[7:]
				break
	s = s.replace(r'\n', '\n')
	return s

#栞を呼び出してメンション返信メッセージ（占いなし）を取得する
def get_message_for_mention_no_fortune(shiori):
	dlldir = os.getcwd()
	if shiori == 'yaya':
		dllpath = r'shiori\yaya\yaya.dll'
		dlldir += r'\shiori\yaya\\'
		enc = 'utf-8'
	s = ''
	subprocess.run(fr'shioricaller\shioricaller.exe {dllpath} {dlldir} < shioricaller\mention_nofortune_request.txt > shioricaller\response.txt', shell=True)
	with open(r'shioricaller\response.txt', encoding=enc) as f:
		for line in f:
			if line.startswith('Value: '):
				s = line[7:]
				break
	s = s.replace(r'\n', '\n')
	return s

#Mastodonのメンション通知一覧を取得する
def get_mentions(mastodon_url, access_token):
	url = f'{mastodon_url}api/v1/notifications'
	headers = {'Authorization': f'Bearer {access_token}'}
	r = requests.get(url, headers=headers, params=[('types[]', 'mention')])
	r.raise_for_status()
	return r.json()

#Mastodonの通知を既読にする
def dismiss_notification(mastodon_url, access_token, notification_id):
	url = f'{mastodon_url}api/v1/notifications/{notification_id}/dismiss'
	headers = {'Authorization': f'Bearer {access_token}'}
	r = requests.post(url, headers=headers)
	r.raise_for_status()

#Mastodonへ投稿する
def post_entry(mastodon_url, access_token, status, visibility='unlisted', in_reply_to_id=None, mention_to=None):
	url = f'{mastodon_url}api/v1/statuses'
	headers = {'Authorization': f'Bearer {access_token}'}
	if mention_to:
		status = f'@{mention_to} {status}'
	payload = {'status': status, 'visibility': visibility}
	if in_reply_to_id:
		payload['in_reply_to_id'] = in_reply_to_id
	r = requests.post(url, data=payload, headers=headers)
	r.raise_for_status()

if __name__ == '__main__':
	#使用する栞
	shiori = sys.argv[1]
	#モード: toot（定期投稿）またはreply（メンション返信）
	mode = sys.argv[2] if len(sys.argv) > 2 else 'toot'
	#投稿先のMastodonのURL
	mastodon_url = 'https://ukadon.shillest.net/'
	#アクセストークン これはGitHubのSettingでActions secretsを設定しておきます ナイショの文字列なので
	access_token = os.getenv('MASTODON_ACCESS_TOKEN')
	#公開範囲 public(公開), unlisted(未収載), private(フォロワーのみ), direct(指定された相手のみ) (directは宛先も必要)
	visibility = 'unlisted'

	if mode == 'reply':
		#メンション返信モード
		mentions = get_mentions(mastodon_url, access_token)
		if not mentions:
			print('返信すべきメンションはありませんでした。')
		for notification in mentions:
			status_obj = notification['status']
			in_reply_to_id = status_obj['id']
			mention_to = status_obj['account']['acct']
			notification_id = notification['id']
			content = status_obj.get('content', '')
			#「占って」が含まれるかで返信内容を切り替える
			if '占って' in content:
				reply_text = get_message_for_mention(shiori)
			else:
				reply_text = get_message_for_mention_no_fortune(shiori)
			post_entry(mastodon_url, access_token, reply_text,
				visibility=visibility,
				in_reply_to_id=in_reply_to_id,
				mention_to=mention_to)
			dismiss_notification(mastodon_url, access_token, notification_id)
			print(f'@{mention_to} へ返信しました: {reply_text}')
	else:
		#定期投稿モード
		status = get_message(shiori)
		post_entry(mastodon_url, access_token, status, visibility)
		print(f'正常に {status} と投稿できました。')
