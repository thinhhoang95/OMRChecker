# !echo -e "\n \t Cloning OMRChecker..."
# !git clone https://github.com/Udayraj123/OMRChecker && cd OMRChecker/  && git checkout google-colab && chmod +x ./setup.sh && ./setup.sh
echo -e "\n \t Installing necessary libs..."
apt-get -qq install -y libsm6 libxext6
apt-get install -y build-essential cmake unzip pkg-config
apt-get install -y libjpeg-dev libpng-dev libtiff-dev
apt-get install -y libavcodec-dev libavformat-dev libswscale-dev libv4l-dev
apt-get install -y libatlas-base-dev gfortran

echo -e "\n \t Installing Opencv..."
python3 -m pip install --user --upgrade pip
python3 -m pip install --user opencv-python
python3 -m pip install --user opencv-contrib-python

echo -e "\n \t Installing Dependencies..."
cd OMRChecker/
python3 -m pip install --user -r requirements.txt