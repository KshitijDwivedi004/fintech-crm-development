#include <bits/stdc++.h>
using namespace std;
int main(){
    // Case 1: [1,2,3,4,5]
    // Case 2: 1 2 3 4 5
    // Case 3: 1,2,3,4,5
    // Case with size not given
    string s;
    while (cin >> s )
    {
        cout<<s;
    }
    

    cout<<"**************";
    vector<int> num;
    string str;
    getline(cin,str);
    stringstream ss(str);
    char ch;
    while (ss >> ch)
    {
        if(ch != ',' || ch != '[' || ch != ']'){
            int n;
            ss >> n;
            num.push_back(n);
        }
    }
    for(auto &x: num)cout<<x<<" ";
    

return 0;
}