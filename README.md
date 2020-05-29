# Seq2seq Chatbot
A conversational agent (chatbot) is a piece of software that is able to communicate with humans using Deep NLP.
A sequence2sequence chatbot implementation with TensorFlow.

# Dependencies
The following python packages are used in seq2seq-chatbot: (excluding packages that come with Anaconda)

  A)TensorFlow 1.0.0 *Note - TF 2.x is not yet supported, use the latest TF 1.0.0 version.
  
  You first need to create virtual environment inside anaconda in which you have to install tensorflow 1.0.0.
  Follow the following steps to create virtual environment and install tensorflow
  
  1.Open terminal an type following command to create virtual environment named "chatbot"
  
        conda create -n chatbot python=3.5
    
  2.Activate environment using command
  
        source activate chatbot

  3.Install tensorflow 1.0.0 using following command
  
        pip install tensorflow==1.0.0
    
  4.Install spyder using command
  
        conda install spyder

  5.Use following command to see installed packages
  
        pip freeze
        
        
# Adding dataset
  Dataset used here is cornell movie corpus dataset.Dataset can be download from the same repository.
  Dataset zip
      cornell_movie_dialogs_corpus.zip
      
  Download and unzip zip.Following two files used for training
    1.movie_lines.txt
    2.movie_conversations.txt

