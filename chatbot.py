


#importing libraries
import numpy as np
import tensorflow as tf
import re
import time


###################  PART 1 -  preprocessing #####################

lines= open('movie_lines.txt').read().split('\n')
conversations= open('movie_conversations.txt').read().split('\n')

#Creating a dictionary that maps each line with user

id2line={}
for line in lines:
    _line=line.split(' +++$+++ ')
    if len(_line)==5:
        id2line[_line[0]]=_line[4]

  #Create a list of conversations

conversations_ids=[]
for conversation in conversations[:-1]:
    _conversation=conversation.split(' +++$+++ ')[-1][1:-1].replace("'","").replace(" ","")
    conversations_ids.append(_conversation.split(","))
 
#Getting separately the questions and answers
questions=[]
answers=[]
for conversation in conversations_ids:
    for i in range(len(conversation)-1):
        questions.append(id2line[conversation[i]])
        answers.append(id2line[conversation[i+1]])
        
        
     
        
    #Doing first cleaning of text
        
def clean_text(text):
    text=text.lower()
    text=re.sub(r"i'm","i am",text)
    text=re.sub(r"he's","he is",text)
    text=re.sub(r"she's","she is",text)
    text=re.sub(r"that's","that is",text)
    text=re.sub(r"what's","what is",text)
    text=re.sub(r"where's","where is",text)
    text=re.sub(r"\'ll"," will",text)
    text=re.sub(r"\'ve"," have",text)
    text=re.sub(r"\'re"," are",text)
    text=re.sub(r"\'d"," would",text)
    text=re.sub(r"won't","will not",text)
    text=re.sub(r"can't","cannot",text)
    text=re.sub(r"it's","it is",text)
    text=re.sub(r"there's","there is",text)
    text=re.sub(r"don't","do not",text)
    text=re.sub(r"let's","let is",text)
    text=re.sub(r"didn't","did not",text)
    text=re.sub(r"you'r","you are",text)
    text=re.sub(r"weren't","were not",text)
    text=re.sub(r"wouldn't","would not",text)


    
    text=re.sub(r"[-()\"#/@;:<>{}+=~|.?,]","",text)
    #text = re.sub(r"\.","",text)

    return text

#cleaning the questions   
clean_questions=[]
for question in questions:
    clean_questions.append(clean_text(question))
    
#cleaning the questions    
clean_answers=[]
for answer in answers:
    clean_answers.append(clean_text(answer))
    
 #creating a dictionary that maps each word to its number of occurances
    
word2count={}
for question in clean_questions:
    for word in question.split():
        if word not in word2count:
            word2count[word]=1
        else:
            word2count[word]+=1
            
for answer in clean_answers:
    for word in answer.split():
        if word not in word2count:
            word2count[word]=1
        else:
            word2count[word]+=1
 
    #Creating two dictinaries that map the questions words and the answers words to unique integer
        
threshold=20        
questions_word2int={}
word_number=0

for word,count in word2count.items():
    if count>threshold:
        questions_word2int[word]=word_number
        word_number+=1
        
answers_word2int={}
word_number=0

for word,count in word2count.items():
    if count>threshold:
        answers_word2int[word]=word_number
        word_number+=1
        
#adding the last tokens to these two dictinaries
    
tokens=['<PAD>','<EOS>','<OUT>','<SOS>']
for token in tokens:
    questions_word2int[token]=len(questions_word2int)+1
    answers_word2int[token]=len(answers_word2int)+1
    
    #creating inverse dictionary of the answers_word2int dictionary
    
answers_int2word={w_i:w for w, w_i in answers_word2int.items()}

#add the end of string token to end of every answer
for i in range(len(clean_answers)):
    clean_answers[i]+=' <EOS>'
  
    #translating all the questions and the answers into integers
  #  and replacing all the words that were filtered out by <OUT>
    
questions_to_int=[]

for question in clean_questions:
    ints=[]
    for word in question.split():
        if word not in questions_word2int:
            ints.append(questions_word2int['<OUT>'])
        else:
            ints.append(questions_word2int[word])
    questions_to_int.append(ints)


answers_to_int=[]

for answers in clean_answers:
    ints=[]
    for word in answer.split():
        if word not in answers_word2int:
            ints.append(answers_word2int['<OUT>'])
        else:
            ints.append(answers_word2int[word])
    answers_to_int.append(ints)


#sorting questions and answers by length
    
sorted_clean_questions=[]
sorted_clean_answers=[]

for length in range(1,25+1):
    for i in enumerate(questions_to_int):
        if len(i[1])==length:
            sorted_clean_questions.append(questions_to_int[i[0]])
            sorted_clean_answers.append(answers_to_int[i[0]])
   
    ############ Part 2 - BUILDING THE SEQ2SEQ MODEL ###################

#creating placeholder for inputs and the targets
            
def model_inputs():
    inputs=tf.placeholder(tf.int32,[None,None],name='input')
    targets=tf.placeholder(tf.int32,[None,None],name='output')
    lr=tf.placeholder(tf.float32,name='learning_rate')
    keep_prob=tf.placeholder(tf.float32,name='keep_prob')
    return inputs,targets,lr,keep_prob
 
#Prepprocessing the targets -cteating batches of ans ,convert into matrix of int
def preprocess_targets(targets, word2int , batch_size):
    left_side = tf.fill([batch_size ,1], word2int['<SOS>'])
    right_side =  tf.strided_slice(targets , [0,0] , [batch_size , -1], [1,1]) 
    preprocessed_targets = tf.concat([left_side , right_side], 1)
    return preprocessed_targets

#Creating the encoder RNN layer
def encoder_rnn(rnn_inputs, rnn_size, num_layers, keep_prob,sequence_length):
    lstm = tf.contrib.rnn.BasicLSTMCell(rnn_size)
    lstm_dropout = tf.contrib.rnn.DropoutWrapper(lstm, input_keep_prob = keep_prob)
    encoder_cell = tf.contrib.rnn.MultiRNNCell([lstm_dropout] * num_layers)
    encoder_output , encoder_state = tf.nn.bidirectional_dynamic_rnn(cell_fw = encoder_cell,
                                                        cell_bw = encoder_cell,
                                                        sequence_length = sequence_length,
                                                        inputs = rnn_inputs,
                                                        dtype = tf.float32)
    return encoder_state

#Decoding the training set


def decode_training_set(encoder_state, decoder_cell, decoder_embeded_input, sequence_length, decoding_scope, output_function, keep_prob,batch_size):
    attention_states= tf.zeros([batch_size, 1, decoder_cell.output_size])
    attention_keys, attention_values, attention_score_function, attention_construct_function = tf.contrib.seq2seq.prepare_attention(attention_states, attention_option= 'bahdanau', num_units= decoder_cell.output_size)
    training_decoder_function= tf.contrib.seq2seq.attention_decoder_fn_train(encoder_state[0],
                                                                             attention_keys,
                                                                             attention_values,
                                                                             attention_score_function,
                                                                             attention_construct_function,
                                                                             name = "attn_dec_train")
    decoder_output, decoder_final_state, decoder_final_context_state = tf.contrib.seq2seq.dynamic_rnn_decoder(decoder_cell,
                                                                                                              training_decoder_function,
                                                                                                              decoder_embeded_input,
                                                                                                              sequence_length,
                                                                                                              scope=decoding_scope)
    decoder_output_dropout = tf.nn.dropout(decoder_output, keep_prob)
    return output_function(decoder_output_dropout)


#Decoding the test / validation set 

def decode_test_set(encoder_state, decoder_cell, decoder_embeddings_matrix, sos_id, eos_id, maximum_length, num_words, decoding_scope, output_function, keep_prob, batch_size):
    attention_states= tf.zeros([batch_size, 1, decoder_cell.output_size])
    attention_keys, attention_values, attention_score_function, attention_construct_function =tf.contrib.seq2seq.prepare_attention(attention_states, attention_option= 'bahdanau', num_units= decoder_cell.output_size)
    test_decoder_function= tf.contrib.seq2seq.attention_decoder_fn_inference(output_function,
                                                                             encoder_state[0],
                                                                             attention_keys,
                                                                             attention_values,
                                                                             attention_score_function,
                                                                             attention_construct_function,
                                                                             decoder_embeddings_matrix,
                                                                             sos_id, 
                                                                             eos_id, 
                                                                             maximum_length, 
                                                                             num_words,
                                                                             name = "attn_dec_inf")
    test_predictions, decoder_final_state, decoder_final_context_state = tf.contrib.seq2seq.dynamic_rnn_decoder(decoder_cell,
                                                                                                                test_decoder_function,
                                                                                                                scope=decoding_scope)
    return test_predictions




#creating the decoder rnn
def decoder_rnn(decoder_embedded_input, decoder_embeddings_matrix, encoder_state, num_words, sequence_length, rnn_size, num_layers, word2int, keep_prob, batch_size):
    with tf.variable_scope("decoding") as decoding_scope:
        lstm = tf.contrib.rnn.BasicLSTMCell(rnn_size)
        lstm_dropout = tf.contrib.rnn.DropoutWrapper(lstm, input_keep_prob = keep_prob)
        decoder_cell = tf.contrib.rnn.MultiRNNCell([lstm_dropout] * num_layers)
        weights = tf.truncated_normal_initializer(stddev = 0.1)
        biases = tf.zeros_initializer()
        output_function = lambda x: tf.contrib.layers.fully_connected(x,
                                                                      num_words,
                                                                      None,
                                                                      scope = decoding_scope,
                                                                      weights_initializer = weights,
                                                                      biases_initializer = biases)
        training_predictions = decode_training_set(encoder_state,
                                                   decoder_cell,
                                                   decoder_embedded_input,
                                                   sequence_length,
                                                   decoding_scope,
                                                   output_function,
                                                   keep_prob,
                                                   batch_size)
        decoding_scope.reuse_variables()
        test_predictions = decode_test_set(encoder_state,
                                           decoder_cell,
                                           decoder_embeddings_matrix,
                                           word2int['<SOS>'],
                                           word2int['<EOS>'],
                                           sequence_length-1,
                                           num_words,
                                           decoding_scope,
                                           output_function,
                                           keep_prob,
                                           batch_size)
        
        return training_predictions, test_predictions

   #building the seq2seq model
def seq2seq_model(inputs, targets, keep_prob, batch_size, sequence_length, answers_num_words, questions_num_words, encoder_embedding_size, decoder_embedding_size, rnn_size, num_layers, questionsword2int):
    encoder_embedded_input = tf.contrib.layers.embed_sequence(inputs, 
                                                              answers_num_words+1,
                                                              encoder_embedding_size,
                                                              initializer = tf.random_uniform_initializer(0,1),
                                                              )
    encoder_state = encoder_rnn(encoder_embedded_input, rnn_size, num_layers, keep_prob, sequence_length)
    preprocessed_targets =preprocess_targets(targets, questionsword2int, batch_size)
    decoder_embeddings_matrix = tf .Variable(tf.random_uniform([questions_num_words+1, decoder_embedding_size], 0, 1))
    decoder_embedded_input = tf.nn.embedding_lookup(decoder_embeddings_matrix, preprocessed_targets)
    training_predictions, test_predictions = decoder_rnn(decoder_embedded_input, 
                                                         decoder_embeddings_matrix,
                                                         encoder_state,
                                                         questions_num_words,
                                                         sequence_length,
                                                         rnn_size,
                                                         num_layers,
                                                         questionsword2int,
                                                         keep_prob,
                                                         batch_size)
    return training_predictions, test_predictions








######################################################################### Copy trainning here 
###################### Part 3 - TRAINING THE SEQ2SEQ MODEL ######################


#setting the hypoparameters
epochs = 60 
batch_size = 42
rnn_size = 512
num_layers = 3
encoding_embedding_size = 512
decoding_embedding_size = 512
learning_rate = 0.01
learning_rate_decay = 0.9
min_learning_rate = 0.0001 
keep_probability = 0.5         #20% of input unites and 50% of hidden units is optimal by research paper "Dropout : A Simple Way To Prevent NN From Overfitting" by Geoffrey Hilton



#defining a session
tf.reset_default_graph()
session = tf.InteractiveSession()

#loading the model inputes
inputs, targets, lr, keep_prob = model_inputs()

#setting the sequense length 
sequence_length = tf.placeholder_with_default(25, None, name = 'sequence_length')

#getting the shape of the inputes tensor
input_shape = tf.shape(inputs)




#gettion training and test predictions
training_predictions , test_predictions = seq2seq_model(tf.reverse(inputs, [-1]),
                                                         targets,
                                                         keep_prob,
                                                         batch_size,
                                                         sequence_length,
                                                         len(answers_word2int),
                                                         len(questions_word2int),
                                                         encoding_embedding_size,
                                                         decoding_embedding_size,
                                                         rnn_size,
                                                         num_layers,
                                                         questions_word2int
                                                         )




#setting up the loss error,the optimiser and gradient clipping
with tf.name_scope("optimization"):
    loss_error = tf.contrib.seq2seq.sequence_loss(training_predictions,
                                                  targets,
                                                  tf.ones([input_shape[0], sequence_length]))
    optimizer = tf.train.AdamOptimizer(learning_rate)
    gradients = optimizer.compute_gradients(loss_error)
    clipped_gradients = [( tf.clip_by_value(grad_tensor , -5., 5.), grad_variable) for grad_tensor , grad_variable in gradients if grad_tensor is not None]
    optimizer_gradient_clipping = optimizer.apply_gradients(clipped_gradients)
 
    
    
#padding the sequence with the <PAD>token
#Questions :[ 'Who','are','you',<PAD>,<PAD>,<PAD>,<PAD>,<PAD> ]
#Answer:[<SOS>,'I','am','a','bot' '.',<EOS>,<PAD  > ]
#paddint tokens are added so length of que and ans matches

def apply_padding(batch_of_sequences,word2int):
    max_sequence_length = max([len(sequence)for sequence in batch_of_sequences])
    return [sequence + [word2int['<PAD>']] * (max_sequence_length-len(sequence)) for sequence in batch_of_sequences]



#splitting the data into batches of question and answers
 
def split_into_batches(questions,answers,batch_size):
    for batch_index in range(0,len(questions)//batch_size):
        start_index = batch_index * batch_size
        questions_in_batch = questions[start_index : start_index + batch_size]
        answers_in_batch = answers[start_index : start_index + batch_size]
        padded_questions_in_batch = np.array(apply_padding( questions_in_batch, questions_word2int))
        padded_answers_in_batch = np.array(apply_padding(answers_in_batch, answers_word2int))
        yield padded_questions_in_batch, padded_answers_in_batch
        
        
        
#split questions and answers into trainning and validation sets
        
training_validation_split = int(len(sorted_clean_questions) * 0.15)
training_questions = sorted_clean_questions[training_validation_split : ]
training_answers = sorted_clean_answers[training_validation_split : ]
validation_questions = sorted_clean_questions[ : training_validation_split]
validation_answers = sorted_clean_answers[ : training_validation_split]
      








   #######      TRAINING         ########
        
batch_index_check_training_loss = 100
batch_index_check_validation_loss = ( (len(training_questions)) //batch_size //2 ) - 1
total_training_loss_error = 0
list_validation_loss_error = []    #=0 error
early_stopping_check = 0
early_stopping_stop = 1000
check_point = "chatbot_weight.ckpt"
session.run(tf.global_variables_initializer())


for epoch in range(1,epochs+1):
    for batch_index, (padded_questions_in_batch,padded_answers_in_batch) in enumerate(split_into_batches(training_questions,training_answers,batch_size)):
        starting_time=time.time()
        _,batch_training_loss_error = session.run([optimizer_gradient_clipping,loss_error],{inputs : padded_questions_in_batch,
                                                                                            targets : padded_answers_in_batch,
                                                                                            lr : learning_rate,
                                                                                            sequence_length : padded_answers_in_batch.shape[1],
                                                                                            keep_prob : keep_probability})
        total_training_loss_error += batch_training_loss_error
        ending_time = time.time()
        batch_time = ending_time - starting_time
        
        if batch_index % batch_index_check_training_loss == 0:
            print('Epoc: {:>3}/{}, Batch: {:>4}/{},Training Loss Error: {:>6.3f}, Training Time on 100 Batches: {:d} seconds'.format(epoch,
                                                                                                                                     epochs,
                                                                                                                                     batch_index,
                                                                                                                                     len(training_questions) // batch_size,
                                                                                                                                     total_training_loss_error / batch_index_check_training_loss,
                                                                                                                                     int(batch_time *batch_index_check_training_loss)))
            total_training_loss_error=0
            
        if batch_index % batch_index_check_validation_loss == 0 and batch_index > 0:
            total_validation_loss_error = 0
            starting_time=time.time()
            for batch_index_validation, (padded_questions_in_batch,padded_answers_in_batch) in enumerate(split_into_batches(validation_questions,validation_answers,batch_size)):
                batch_validation_loss_error = session.run(loss_error,{inputs : padded_questions_in_batch,
                                                                      targets : padded_answers_in_batch,
                                                                      lr : learning_rate,
                                                                      sequence_length : padded_answers_in_batch.shape[1],
                                                                      keep_prob : 1})
                total_validation_loss_error += batch_validation_loss_error
            ending_time = time.time()
            batch_time = ending_time - starting_time
            avrage_validation_loss_error = total_validation_loss_error / (len(validation_questions) / batch_size)
            print('Validation Loss Error: {:>6.3f},Batch Validation Time: {:d} seconds'.format(avrage_validation_loss_error,int(batch_time)))
            
            learning_rate *=learning_rate_decay
            if learning_rate< min_learning_rate:
                learning_rate=min_learning_rate
            list_validation_loss_error.append(avrage_validation_loss_error)
            if avrage_validation_loss_error<=min(list_validation_loss_error):
                print('I speak better now !')
                early_stopping_check = 0
                saver = tf.train.Saver()
                saver.save(session,check_point)
            else:
                print("Sorry I do not speak better,I need to practice more.")
                early_stopping_check+=1
                if early_stopping_check == early_stopping_stop:
                    break
    if early_stopping_check == early_stopping_stop:
         print("My apologies, I cannot speak better anymore, this is best I can do.")
         break
print('Game Over')




"""
######### Part 4- Testing the seq2seq model ############

check_point = "./chatbot_weight.ckpt"
session = tf.InteractiveSession()
session.run(tf.global_variables_initializer())
saver = tf.train.Saver()
saver.restore(session , check_point)

# Convertiong the list of questions from string to list of encoding integers
def convert_string2int(question , word2int):
    question = clean_text(question)
    return [word2int.get(word , word2int['<OUT>']) for word in question.split() ]

# Setting up the chat
while True:
    question = raw_input(' You : ')
    if question == 'Goodbye' or question == 'goodbye' or question == 'bye' or question == 'Bye':
        print('Bye')
        break
    
    question = convert_string2int( question , questions_word2int)
    question = question + [questions_word2int['<PAD>']] * (20 - len(question))
    fake_batch = np.zeros((batch_size , 20))
    fake_batch[0] = question
    predicted_answer = session.run(test_predictions , {inputs : fake_batch , keep_prob : 0.5})[0]
    answer = ''
    for i in np.argmax(predicted_answer , 1):
        if answers_int2word[i] == 'i':
            token = 'I'
        elif answers_int2word[i] == '<EOS>':
            token = '.'
        elif answers_int2word[i] == '<OUT>':
            token = 'out'
        else:
            token = ' '+ answers_int2word[i]
        answer += token
        if token == '.':
            break
        
    print(" Chatbot : "+ answer)
    
"""    



 












