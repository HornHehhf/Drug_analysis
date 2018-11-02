

def evaluate_item(items, ref_items, accuracy_dict, count_dict, pred_count, fout, val_count):
	for index in range(len(items[key])):
		item = items[key][index]
		ref_item = ref_items[key][index]
		val_count += 1
		correct_dict = {}
		for cur_key in accuracy_dict.keys():
			correct_dict[cur_key] = "wrong"
		for cur_key in accuracy_dict.keys():
			# add def minority for ref
			if cur_key == 'def.minority':
				if ref_item['def.ethnicity'] == '汉族' or ref_item['def.ethnicity'] == "":
					ref_item['def.minority'] = 0
				else:
					ref_item['def.minority'] = 1
			if cur_key == 'def.recid' and ref_item[cur_key] == "":
				ref_item[cur_key] = "0"
			# change blank to 0 for recid
			if ref_item[cur_key] == item[cur_key]:
				correct_dict[cur_key] = "correct"
			if item[cur_key] != '':
				pred_count[cur_key] += 1
			if ref_item[cur_key] != '':
				# revise the def prev name
				if cur_key == 'def.name.prev':
					def_name = ref_item[cur_key]
					pattern = '(曾用名|别名|绰号|自称|别名|外号|经名|化名|又名|汉名|小名)([:：“])?([\u2e80-\u9fff]+)[,，)]?'
					match = re.search(pattern, def_name)
					if match is not None:
						ref_item['def.name.prev'] = match.group(3)
				count_dict[cur_key] += 1
				if item[cur_key] == ref_item[cur_key]:
					accuracy_dict[cur_key] += 1
					correct_dict[cur_key] = 'correct'
			if 'quantity' in cur_key and item[cur_key] != ref_item[cur_key]:
				fout_error.write(item['doc'] + "\n")
				fout_error.write(cur_key + "\n")
				fout_error.write('pred: ' + str(item[cur_key]) + "\n")
				fout_error.write('ref: ' + str(ref_item[cur_key]) + "\n")
				
		fout.write('doc: ' + item['doc'] + "\n")
		for cur_key in current_focus[1:]:
			fout.write(cur_key + ': ' + str(item[cur_key]) + " vs " + str(ref_item[cur_key]) + " " + correct_dict[cur_key]
					   + "\n")
		fout.write("\n")