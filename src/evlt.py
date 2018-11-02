import re

def evaluate_item(key, items, ref_items, accuracy_dict, count_dict, pred_count, val_count, fout, fout_error, current_focus):
	for index in range(len(items[key])):
		item = items[key][index]
		ref_item = ref_items[key][index]
		val_count += 1
		correct_dict = {}
		for cur_key in accuracy_dict.keys():
			correct_dict[cur_key] = "wrong"
		for cur_key in accuracy_dict.keys():
			# add def minority for ref
			ref_item = add_def_minority_ref(cur_key, ref_item)
			if cur_key == 'def.recid' and ref_item[cur_key] == "":
				ref_item[cur_key] = "0"
			# change blank to 0 for recid
			if ref_item[cur_key] == item[cur_key]:
				correct_dict[cur_key] = "correct"
			if item[cur_key] != '':
				pred_count[cur_key] += 1
			if ref_item[cur_key] != '':
				# revise the def prev name
				ref_item = revise_prev_name(cur_key, ref_item)
				
				count_dict[cur_key] += 1
				if item[cur_key] == ref_item[cur_key]:
					accuracy_dict[cur_key] += 1
					correct_dict[cur_key] = 'correct'
			write_fout_error(cur_key, item[cur_key], ref_item[cur_key], item['doc'], fout_error)
			
				
		write_fout(item, ref_item, current_focus, correct_dict, fout)

	return (accuracy_dict, count_dict, pred_count, val_count)


def write_fout(item, ref_item, current_focus, correct_dict, fout):
	fout.write('doc: ' + item['doc'] + "\n")
	for cur_key in current_focus[1:]:
		fout.write(cur_key + ': ' + str(item[cur_key]) + " vs " + str(ref_item[cur_key]) + " " + correct_dict[cur_key]
				   + "\n")
	fout.write("\n")

def write_fout_error(cur_key, item, ref_item, item_doc, fout_error):
	if 'quantity' in cur_key and item != ref_item:
		fout_error.write(item_doc + "\n")
		fout_error.write(cur_key + "\n")
		fout_error.write('pred: ' + str(item) + "\n")
		fout_error.write('ref: ' + str(ref_item) + "\n")

def revise_prev_name(cur_key, ref_item):
	if cur_key == 'def.name.prev':
		def_name = ref_item[cur_key]
		pattern = '(曾用名|别名|绰号|自称|别名|外号|经名|化名|又名|汉名|小名)([:：“])?([\u2e80-\u9fff]+)[,，)]?'
		match = re.search(pattern, def_name)
		if match is not None:
			ref_item['def.name.prev'] = match.group(3)
	return ref_item

def add_def_minority_ref(cur_key, ref_item):
	if cur_key == 'def.minority':
		if ref_item['def.ethnicity'] == '汉族' or ref_item['def.ethnicity'] == "":
			ref_item['def.minority'] = 0
		else:
			ref_item['def.minority'] = 1
	return ref_item

def write_scores(current_focus, accuracy_dict, pred_count, count_dict, fout):
	for key in current_focus[1:]:
		recall = 0.0
		precision = 0.0
		f1_score = 0.0
		if accuracy_dict[key] != 0:
			precision = accuracy_dict[key]/pred_count[key]
			recall = accuracy_dict[key]/count_dict[key]
		if precision + recall != 0:
			f1_score = 2 * precision * recall / (precision + recall)
		res_dict = {'precision': precision, 'recall': recall, 'f1_score': f1_score, 'correct num': accuracy_dict[key],
					'pred num': pred_count[key], 'gold num': count_dict[key]}
		fout.write(key + ":\n")
		fout.write(str(res_dict) + "\n")
