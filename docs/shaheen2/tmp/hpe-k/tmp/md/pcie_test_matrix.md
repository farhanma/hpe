| Cable | Connection   | Gbps | Type       | CPU   | Max Size | Result |
| :---: | :----------: | :--: | :--------: | :---: | :------: | :----: |
| HDR   | switch       | 200  | GPU-to-GPU | 7713P | 2^23     | fail   |
| HDR   | back-to-back | 200  | GPU-to-GPU | 7713P | 2^23     | fail   |
| EDR   | back-to-back | 100  | GPU-to-GPU | 7713P | 2^23     | pass   |
| EDR   | switch       | 100  | GPU-to-GPU | 7713P | 2^23     | pass   |
| HDR   | back-to-back | 100  | GPU-to-GPU | 7713P | 2^23     | pass   |
| HDR   | switch       | 100  | GPU-to-GPU | 7713P | 2^23     | pass   |
| HDR   | switch       | 200  | GPU-to-GPU | 7713P | 2^15     | pass   |
| HDR   | switch       | 200  | CPU-to-CPU | 7713P | 2^23     | pass   |
| EDR   | back-to-back | 100  | CPU-to-CPU | 7713P | 2^23     | pass   |
